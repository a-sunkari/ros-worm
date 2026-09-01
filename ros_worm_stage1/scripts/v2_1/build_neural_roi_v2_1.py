#!/usr/bin/env python3
"""Build and QC resolution-convergent analysis-only nervous ROIs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import trimesh
import vtk
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from neural_roi import (  # noqa: E402
    SparseVoxelROI, enclosed_points, grid_definition, load_member_surfaces,
    resolve_repo_path, sparse_connectivity, stl_polydata, voxelize_member,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def portable_path(path: Path, repo: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo.resolve()))
    except ValueError:
        return str(resolved)


def closest_distances(points: np.ndarray, surface: vtk.vtkPolyData) -> np.ndarray:
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(surface)
    locator.BuildLocator()
    result = np.empty(len(points), dtype=float)
    cell = vtk.vtkGenericCell()
    for index, point in enumerate(points):
        target = [0.0, 0.0, 0.0]
        cell_id, sub_id, distance2 = vtk.reference(0), vtk.reference(0), vtk.reference(0.0)
        locator.FindClosestPoint(point, target, cell, cell_id, sub_id, distance2)
        result[index] = float(distance2) ** 0.5
    return result


def actual_member_qc(source_manifest: Path, repo: Path) -> pd.DataFrame:
    table = pd.read_csv(source_manifest)
    rows = []
    for record in table[table["category_guess"] == "NervousSystem"].itertuples(index=False):
        path = resolve_repo_path(record.stl_path, repo)
        # Binary STL duplicates vertices per facet.  Merge coincident vertices
        # before topology checks; otherwise every valid STL appears open.
        mesh = trimesh.load_mesh(path, force="mesh", process=True)
        rows.append({"object_name": record.object_name, "path": portable_path(path, repo), "sha256": sha256(path),
                     "faces": len(mesh.faces), "vertices": len(mesh.vertices),
                     "watertight_actual": bool(mesh.is_watertight),
                     "winding_consistent_actual": bool(mesh.is_winding_consistent),
                     "signed_volume_model_units3": float(mesh.volume)})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--reference-stl", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pitches-um", default="0.25,0.5,1,2")
    parser.add_argument("--density-g-cm3", type=float, default=1.04)
    parser.add_argument("--surface-samples", type=int, default=30_000)
    parser.add_argument("--seed", type=int, default=20260831)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    args.outdir.mkdir(parents=True, exist_ok=True)

    source_manifest = args.source_manifest.resolve()
    placement_manifest = args.placement_manifest.resolve()
    reference_path = args.reference_stl.resolve()
    member_qc = actual_member_qc(source_manifest, repo)
    member_qc.to_csv(args.outdir / "neural_source_member_qc.csv", index=False)
    if not member_qc["watertight_actual"].all() or not member_qc["winding_consistent_actual"].all():
        raise SystemExit("Source-member union invalid: at least one member is not closed and consistently wound")

    members, center_model, body = load_member_surfaces(source_manifest, placement_manifest, repo)
    reference = stl_polydata(reference_path, center_model, 100.0)
    reference_bounds = np.asarray(reference.GetBounds(), dtype=float).reshape(3, 2)
    member_bounds = np.stack([item["bounds_um"] for item in members])
    union_bounds = np.column_stack([member_bounds[:, :, 0].min(axis=0), member_bounds[:, :, 1].max(axis=0)])

    reference_mesh = trimesh.load_mesh(reference_path, force="mesh", process=False)
    rng = np.random.default_rng(args.seed)
    reference_sample_model, _ = trimesh.sample.sample_surface(reference_mesh, args.surface_samples, seed=args.seed)
    reference_sample_um = (reference_sample_model - center_model[None, :]) * 100.0

    convergence_rows = []
    for pitch in [float(value) for value in args.pitches_um.split(",") if value.strip()]:
        origin_edge, dimensions = grid_definition(union_bounds, pitch)
        member_voxels = []
        for index, member in enumerate(members, start=1):
            occupied = voxelize_member(member, pitch, origin_edge, dimensions)
            if len(occupied):
                member_voxels.append(occupied)
            if index % 50 == 0 or index == len(members):
                print(f"pitch={pitch:g} um: voxelized {index}/{len(members)} members", flush=True)
        union_flat = np.unique(np.concatenate(member_voxels))
        preclip = SparseVoxelROI(pitch, origin_edge, dimensions, union_flat)
        centers = preclip.centers()
        body_inside = enclosed_points(centers, body)
        outside_count = int((~body_inside).sum())
        union_flat = union_flat[body_inside]
        roi = SparseVoxelROI(pitch, origin_edge, dimensions, union_flat)
        component_count, component_sizes, boundary_mask = sparse_connectivity(union_flat, dimensions)
        boundary_flat = union_flat[boundary_mask]
        boundary_centers = roi.centers(boundary_flat)

        sample_count = min(args.surface_samples, len(boundary_centers))
        chosen = rng.choice(len(boundary_centers), sample_count, replace=False)
        candidate_to_reference = closest_distances(boundary_centers[chosen], reference)
        tree = cKDTree(boundary_centers)
        reference_to_candidate = tree.query(reference_sample_um, workers=-1)[0]
        symmetric = np.concatenate([candidate_to_reference, reference_to_candidate])

        path = args.outdir / f"neural_roi_union_members_pitch_{pitch:g}um.npz"
        np.savez_compressed(path, pitch_um=np.asarray(pitch), origin_edge_um=origin_edge,
                            dimensions=dimensions, flat_indices=union_flat,
                            boundary_flat_indices=boundary_flat)
        volume_um3 = len(union_flat) * pitch ** 3
        mass_kg = volume_um3 * 1e-18 * args.density_g_cm3 * 1000.0
        convergence_rows.append({
            "pitch_um": pitch, "occupied_voxels": len(union_flat), "volume_um3": volume_um3,
            "density_g_cm3": args.density_g_cm3, "mass_kg": mass_kg,
            "preclip_occupied_voxels": len(centers), "outside_body_voxels": outside_count,
            "fraction_volume_outside_body_preclip": outside_count / len(centers),
            "twentysix_connected_components": component_count,
            "largest_component_fraction": float(component_sizes.max() / len(union_flat)),
            "boundary_voxels": len(boundary_flat),
            "surface_error_p50_um": float(np.percentile(symmetric, 50)),
            "surface_error_p95_um": float(np.percentile(symmetric, 95)),
            "surface_error_p99_um": float(np.percentile(symmetric, 99)),
            "surface_error_sampled_hausdorff_um": float(symmetric.max()),
            "reference_to_candidate_p95_um": float(np.percentile(reference_to_candidate, 95)),
            "candidate_to_reference_p95_um": float(np.percentile(candidate_to_reference, 95)),
            "roi_file": portable_path(path, repo), "roi_sha256": sha256(path),
        })
        print(json.dumps(convergence_rows[-1], indent=2), flush=True)

    convergence = pd.DataFrame(convergence_rows).sort_values("pitch_um")
    convergence.to_csv(args.outdir / "neural_roi_resolution_convergence.csv", index=False)
    metadata = {
        "method": "voxel-center sampling of the set-theoretic union of 276 individually closed source nervous objects, intersected with the whole-body envelope",
        "interpretation": "analysis-only neural ROI; never placed in Geant4",
        "source_manifest": portable_path(source_manifest, repo), "source_manifest_sha256": sha256(source_manifest),
        "placement_manifest": portable_path(placement_manifest, repo), "placement_manifest_sha256": sha256(placement_manifest),
        "reference_high_resolution_atlas": portable_path(reference_path, repo), "reference_sha256": sha256(reference_path),
        "source_members": len(members), "all_members_watertight_actual": bool(member_qc.watertight_actual.all()),
        "all_members_winding_consistent_actual": bool(member_qc.winding_consistent_actual.all()),
        "body_center_model_units": center_model.tolist(), "um_per_model_unit": 100.0,
        "reference_bounds_um": reference_bounds.tolist(), "member_union_bounds_um": union_bounds.tolist(),
        "density_g_cm3_primary": args.density_g_cm3,
        "density_note": "G4_BRAIN_ICRP proxy; 1.00 g/cm3 is retained as a dose sensitivity case.",
        "surface_error_definition": "sampled symmetric distance between full-resolution baked-union triangle surface and occupied-voxel boundary centers",
        "random_seed": args.seed, "surface_samples_each_direction_max": args.surface_samples,
        "convergence_records": convergence_rows,
    }
    (args.outdir / "neural_roi_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
