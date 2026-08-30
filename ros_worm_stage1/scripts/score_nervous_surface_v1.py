#!/usr/bin/env python3
"""Production nervous-atlas proximity scoring with explicit eligibility filters.

The neural STL is used only as an anatomical surface.  This script never
performs an inside-neuron test and never labels the result nervous absorbed
dose.  VTK's static triangle locator keeps full-resolution queries bounded in
memory, avoiding the large candidate arrays created by the legacy trimesh path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy


def resolve_from_manifest(manifest: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (manifest.parent / path).resolve()


def body_geometry(manifest: Path) -> tuple[Path, np.ndarray]:
    table = pd.read_csv(manifest)
    body = table[(table["safe_name"] == "WholeBodyEnvelope") | (table["category_guess"] == "whole_body_parent")]
    if len(body) != 1:
        raise SystemExit(f"Expected one body row in {manifest}; found {len(body)}")
    body_path = resolve_from_manifest(manifest, str(body.iloc[0]["stl_path"]))
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(body_path)); reader.Update()
    bounds = np.asarray(reader.GetOutput().GetBounds(), dtype=float).reshape(3, 2)
    return body_path, bounds.mean(axis=1)


def transformed_polydata(stl: Path, center_model: np.ndarray, mm_per_unit: float) -> vtk.vtkPolyData:
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(stl)); reader.Update()
    mesh = vtk.vtkPolyData(); mesh.DeepCopy(reader.GetOutput())
    points = vtk_to_numpy(mesh.GetPoints().GetData()).astype(np.float64, copy=True)
    points = (points - center_model[None, :]) * mm_per_unit
    vtk_points = vtk.vtkPoints(); vtk_points.SetData(numpy_to_vtk(points, deep=True))
    mesh.SetPoints(vtk_points); mesh.BuildCells(); mesh.BuildLinks()
    return mesh


def enclosed_points(points_mm: np.ndarray, surface: vtk.vtkPolyData) -> np.ndarray:
    cloud = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints(); vtk_points.SetData(numpy_to_vtk(points_mm, deep=True))
    cloud.SetPoints(vtk_points)
    selector = vtk.vtkSelectEnclosedPoints()
    selector.SetInputData(cloud); selector.SetSurfaceData(surface)
    selector.SetTolerance(1e-8); selector.Update()
    flags = vtk_to_numpy(selector.GetOutput().GetPointData().GetArray("SelectedPoints"))
    return flags.astype(bool)


def closest_surface(points_mm: np.ndarray, surface: vtk.vtkPolyData) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    locator = vtk.vtkStaticCellLocator(); locator.SetDataSet(surface); locator.BuildLocator()
    closest = np.empty_like(points_mm); distance = np.empty(len(points_mm)); cell_ids = np.empty(len(points_mm), dtype=np.int64)
    generic_cell = vtk.vtkGenericCell()
    for i, point in enumerate(points_mm):
        target = [0.0, 0.0, 0.0]; cell_id = vtk.reference(0); sub_id = vtk.reference(0); dist2 = vtk.reference(0.0)
        locator.FindClosestPoint(point, target, generic_cell, cell_id, sub_id, dist2)
        closest[i] = target; distance[i] = float(dist2) ** 0.5; cell_ids[i] = int(cell_id)
    return closest, distance, cell_ids


def find_xyz(df: pd.DataFrame) -> tuple[list[str], float, str]:
    for columns, factor, units in [
        (["x_um", "y_um", "z_um"], 1e-3, "um"),
        (["x_mm", "y_mm", "z_mm"], 1.0, "mm"),
    ]:
        if all(column in df for column in columns): return columns, factor, units
    raise SystemExit("No recognized x/y/z columns")


def write_spectrum(df: pd.DataFrame, energy: str, path: Path, bins: int) -> None:
    values = df[energy].to_numpy(float)
    if len(values) == 0:
        path.write_text("# energy_keV,weight\n")
        return
    upper = max(float(values.max()), 1.0)
    count, edges = np.histogram(values, bins=bins, range=(0.0, upper))
    centers = 0.5 * (edges[1:] + edges[:-1])
    with path.open("w") as handle:
        handle.write("# energy_keV,weight\n")
        for energy_kev, weight in zip(centers, count):
            if weight: handle.write(f"{energy_kev:.9g},{int(weight)}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secondaries", required=True, type=Path)
    parser.add_argument("--nervous-stl", required=True, type=Path)
    parser.add_argument("--placement-manifest", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--mm-per-model-unit", type=float, default=0.1)
    parser.add_argument("--threshold-um", type=float, default=5.0)
    parser.add_argument("--threshold-scan-um", default="0.5,1,2,5,10,25,50")
    parser.add_argument("--bins", type=int, default=120)
    parser.add_argument("--skip-geometric-body-check", action="store_true")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.secondaries)
    xyz, to_mm, units = find_xyz(data)
    points_mm = data[xyz].to_numpy(float) * to_mm
    energy_column = next((name for name in ["ekin_keV", "energy_keV"] if name in data), None)
    if not energy_column: raise SystemExit("No electron energy column")

    body_path, center_model = body_geometry(args.placement_manifest)
    body = transformed_polydata(body_path, center_model, args.mm_per_model_unit)
    nervous = transformed_polydata(args.nervous_stl, center_model, args.mm_per_model_unit)

    is_electron = data["secondaryPDG"].astype(int).eq(11).to_numpy() if "secondaryPDG" in data else np.ones(len(data), bool)
    finite = np.isfinite(points_mm).all(axis=1)
    recorded_inside = data["insideBody"].astype(int).eq(1).to_numpy() if "insideBody" in data else np.ones(len(data), bool)
    if args.skip_geometric_body_check:
        geometric_inside = np.ones(len(data), bool)
    else:
        geometric_inside = np.zeros(len(data), bool)
        candidates = finite & is_electron
        geometric_inside[candidates] = enclosed_points(points_mm[candidates], body)
    eligible = finite & is_electron & recorded_inside & geometric_inside

    closest_all = np.full((len(data), 3), np.nan); distance_mm = np.full(len(data), np.nan); triangle_id = np.full(len(data), -1, dtype=np.int64)
    closest, distances, ids = closest_surface(points_mm[eligible], nervous)
    closest_all[eligible] = closest; distance_mm[eligible] = distances; triangle_id[eligible] = ids
    distance_um = distance_mm * 1000.0

    data["is_electron"] = is_electron
    data["finite_position"] = finite
    data["recorded_inside_body"] = recorded_inside
    data["geometrically_inside_body"] = geometric_inside
    data["eligible_for_neural_proximity"] = eligible
    data["distance_to_nervous_surface_um"] = distance_um
    data["closest_nervous_x_mm"] = closest_all[:, 0]
    data["closest_nervous_y_mm"] = closest_all[:, 1]
    data["closest_nervous_z_mm"] = closest_all[:, 2]
    data["closest_nervous_triangle_id"] = triangle_id
    data["near_nervous_surface"] = eligible & (distance_um <= args.threshold_um)
    data.to_csv(args.outdir / "secondary_records_with_nervous_surface_distance.csv", index=False)

    scored = data[eligible].copy(); near = data[data["near_nervous_surface"]].copy()
    scored.to_csv(args.outdir / "eligible_electrons_with_nervous_surface_distance.csv", index=False)
    near.to_csv(args.outdir / "electrons_near_nervous_surface.csv", index=False)
    write_spectrum(near, energy_column, args.outdir / "electron_spectrum_near_nervous_surface.csv", args.bins)

    scan = []
    valid_dist = distance_um[eligible]
    for threshold in [float(value) for value in args.threshold_scan_um.split(",") if value.strip()]:
        mask = eligible & (distance_um <= threshold)
        scan.append({"threshold_um": threshold, "n_electrons_near": int(mask.sum()), "fraction_of_eligible_electrons": float(mask.sum()/eligible.sum()) if eligible.any() else 0.0})
    pd.DataFrame(scan).to_csv(args.outdir / "nervous_surface_threshold_scan.csv", index=False)

    summary = {
        "method": "exact closest point on the full-resolution nervous triangle surface using vtkStaticCellLocator",
        "interpretation": "surface-proximity shell only; not an inside-neural-volume test and not nervous absorbed dose",
        "secondaries_csv": str(args.secondaries.resolve()), "nervous_stl": str(args.nervous_stl.resolve()),
        "placement_manifest": str(args.placement_manifest.resolve()), "body_stl": str(body_path),
        "mm_per_model_unit": args.mm_per_model_unit, "body_center_model_units": center_model.tolist(),
        "position_columns": xyz, "position_units": units, "n_input_records": int(len(data)),
        "n_non_electron_records_excluded": int((~is_electron).sum()),
        "n_nonfinite_records_excluded": int((~finite).sum()),
        "n_recorded_outside_body": int((is_electron & ~recorded_inside).sum()),
        "n_geometrically_outside_body": int((is_electron & finite & ~geometric_inside).sum()),
        "n_eligible_electrons": int(eligible.sum()), "primary_threshold_um": args.threshold_um,
        "n_near_primary": int((eligible & (distance_um <= args.threshold_um)).sum()),
        "fraction_near_primary": float((eligible & (distance_um <= args.threshold_um)).sum()/eligible.sum()) if eligible.any() else 0.0,
        "distance_um_min": float(valid_dist.min()) if len(valid_dist) else None,
        "distance_um_median": float(np.median(valid_dist)) if len(valid_dist) else None,
        "distance_um_p95": float(np.percentile(valid_dist, 95)) if len(valid_dist) else None,
        "distance_um_max": float(valid_dist.max()) if len(valid_dist) else None,
        "nervous_bounds_mm": list(nervous.GetBounds()), "body_bounds_mm": list(body.GetBounds()),
    }
    (args.outdir / "nervous_surface_scoring_metadata.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2)); print(pd.DataFrame(scan).to_string(index=False))


if __name__ == "__main__":
    main()
