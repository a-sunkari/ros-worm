#!/usr/bin/env python3
"""Final neural ROI membership, mass-unit, and localized outlier audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import trimesh
import vtk
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v2_1"))
from neural_roi import SparseVoxelROI, body_center_and_path, stl_polydata  # noqa: E402


def vtk_distances(points: np.ndarray, surface: vtk.vtkPolyData) -> np.ndarray:
    locator = vtk.vtkStaticCellLocator(); locator.SetDataSet(surface); locator.BuildLocator()
    out = np.empty(len(points)); cell = vtk.vtkGenericCell()
    for i, point in enumerate(points):
        closest = [0.0, 0.0, 0.0]; cid, sid, d2 = vtk.reference(0), vtk.reference(0), vtk.reference(0.0)
        locator.FindClosestPoint(point, closest, cell, cid, sid, d2); out[i] = float(d2) ** 0.5
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--focused", type=Path, required=True)
    parser.add_argument("--diffuse", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260901)
    args = parser.parse_args(); repo = args.repo.resolve(); args.outdir.mkdir(parents=True, exist_ok=True)
    validation = repo / "ros_worm_stage1/validation/v2_1/neural_roi"
    member_qc = pd.read_csv(validation / "neural_source_member_qc.csv")
    source = pd.read_csv(repo / "openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
    nervous = source[source.category_guess == "NervousSystem"]
    if len(nervous) != 276 or len(member_qc) != 276 or not member_qc.watertight_actual.all() or not member_qc.winding_consistent_actual.all():
        raise SystemExit("276-member neural source invariant failed")
    if (member_qc.signed_volume_model_units3 <= 0).any(): raise SystemExit("non-positive neural member interior")
    convergence = pd.read_csv(validation / "neural_roi_resolution_convergence.csv")
    primary = SparseVoxelROI.load(validation / "neural_roi_union_members_pitch_0.25um.npz")
    volume_um3 = len(primary.flat_indices) * primary.pitch_um ** 3
    mass_kg = volume_um3 * 1e-18 * 1040.0

    # Reproduce and localize high-distance surface samples.
    atlas_path = repo / "openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"
    placement = repo / "ros_worm_stage1/config/transport_geometry_v1.csv"
    center, _ = body_center_and_path(placement, repo)
    atlas = stl_polydata(atlas_path, center, 100.0)
    mesh = trimesh.load_mesh(atlas_path, force="mesh", process=False)
    sampled_model, _ = trimesh.sample.sample_surface(mesh, args.samples, seed=args.seed)
    sampled = (sampled_model - center[None, :]) * 100.0
    boundary = primary.centers(np.load(validation / "neural_roi_union_members_pitch_0.25um.npz")["boundary_flat_indices"])
    ref_to_roi = cKDTree(boundary).query(sampled, workers=-1)[0]
    rng = np.random.default_rng(args.seed)
    chosen = rng.choice(len(boundary), min(args.samples, len(boundary)), replace=False)
    roi_to_ref = vtk_distances(boundary[chosen], atlas)
    outlier_rows = []
    for direction, points, distances in (("reference_to_roi", sampled, ref_to_roi),
                                         ("roi_to_reference", boundary[chosen], roi_to_ref)):
        for threshold in (1, 5, 10, 25):
            mask = distances > threshold
            outlier_rows.append({"direction": direction, "threshold_um": threshold,
                                 "sample_points": len(distances), "outlier_points": int(mask.sum()),
                                 "outlier_fraction": float(mask.mean()),
                                 "outlier_y_min_um": float(points[mask, 1].min()) if mask.any() else np.nan,
                                 "outlier_y_median_um": float(np.median(points[mask, 1])) if mask.any() else np.nan,
                                 "outlier_y_max_um": float(points[mask, 1].max()) if mask.any() else np.nan,
                                 "max_distance_um": float(distances.max())})
    pd.DataFrame(outlier_rows).to_csv(args.outdir / "surface_outlier_localization.csv", index=False)

    disagreement_rows = []
    for label, result in (("focused", args.focused), ("diffuse", args.diffuse)):
        score = result / "anatomy_edep_v2_1"
        cache = np.load(score / "edep_step_scoring_cache.npz")
        exact = np.load(score / "exact_member_union_step_membership.npz")["inside"].astype(bool)
        eligible = cache["eligible"].astype(bool); edep = cache["edep_keV"].astype(float)
        points = np.column_stack([cache["scoreX_um"], cache["scoreY_um"], cache["scoreZ_um"]])
        voxel = eligible & primary.contains(points); exact &= eligible
        exact_total = edep[exact].sum()
        for category, mask in (("both", exact & voxel), ("exact_only", exact & ~voxel),
                               ("voxel_only", voxel & ~exact), ("neither", eligible & ~exact & ~voxel)):
            disagreement_rows.append({"irradiation": label, "classification": category,
                                      "steps": int(mask.sum()), "edep_keV": float(edep[mask].sum()),
                                      "edep_percent_of_exact_neural": float(100 * edep[mask].sum() / exact_total)})
    pd.DataFrame(disagreement_rows).to_csv(args.outdir / "exact_voxel_membership_disagreement.csv", index=False)
    metadata = {"source_members": 276, "selected_members_all_manifest_category_nervous": len(nervous) == 276,
                "all_watertight_after_vertex_merge": True, "all_winding_consistent": True,
                "all_positive_signed_interiors": True, "union_overlap_rule": "logical OR; each point/voxel counted once",
                "body_clipping": "voxel centers outside closed body envelope removed before mass calculation",
                "primary_pitch_um": 0.25, "primary_volume_um3": volume_um3, "primary_density_kg_m3": 1040.0,
                "primary_mass_kg": mass_kg, "mass_formula": "volume_um3 * 1e-18 m3/um3 * 1040 kg/m3",
                "volume_range_percent": float(100 * (convergence.volume_um3.max()/convergence.volume_um3.min()-1)),
                "outlier_interpretation": "localized surface-sampling disagreement; scientific impact quantified by exact/voxel edep disagreement"}
    (args.outdir / "neural_roi_final_audit.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
