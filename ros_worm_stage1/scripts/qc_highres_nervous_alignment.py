#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import os, shutil

import numpy as np
import pandas as pd
import trimesh
import plotly.graph_objects as go
import plotly.express as px
from scipy.spatial import cKDTree

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave


def compute_center_from_manifest(manifest: Path):
    df = pd.read_csv(manifest)
    mins, maxs = [], []
    for p in df["stl_path"]:
        m = trimesh.load_mesh(Path(p), force="mesh")
        mins.append(m.bounds[0])
        maxs.append(m.bounds[1])
    return 0.5 * (np.min(np.vstack(mins), axis=0) + np.max(np.vstack(maxs), axis=0))


def find_cols(df):
    if all(c in df.columns for c in ["x_um", "y_um", "z_um"]):
        return ("x_um", "y_um", "z_um"), 1e-3, "µm"
    if all(c in df.columns for c in ["x_mm", "y_mm", "z_mm"]):
        return ("x_mm", "y_mm", "z_mm"), 1.0, "mm"
    raise SystemExit("Could not identify position columns: " + ", ".join(df.columns))


def sample_reference_points(mesh, surface_samples, seed):
    pts = [np.asarray(mesh.vertices, dtype=float)]
    if surface_samples > 0:
        np.random.seed(seed)
        samp, _ = trimesh.sample.sample_surface(mesh, surface_samples)
        pts.append(np.asarray(samp, dtype=float))
    return np.vstack(pts)


def simplify_for_plot(mesh, max_faces):
    if len(mesh.faces) <= max_faces:
        return mesh
    try:
        m = mesh.simplify_quadric_decimation(face_count=max_faces)
        m.remove_unreferenced_vertices()
        return m
    except Exception as e:
        print("[WARN] decimation failed; plotting full mesh may be heavy:", repr(e))
        return mesh


def write(fig, out_base, width=1700, height=950):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=15),
        title=dict(x=0.02, xanchor="left", font=dict(size=24)),
        scene=dict(
            xaxis_title="x (mm)",
            yaxis_title="y (mm)",
            zaxis_title="z (mm)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.55, y=-2.1, z=1.05)),
        ),
        margin=dict(l=0, r=0, t=70, b=0),
    )
    fig.write_html(out_base.with_suffix(".html"), include_plotlyjs="cdn")
    fig.write_image(out_base.with_suffix(".png"), width=width, height=height, scale=2)
    fig.write_image(out_base.with_suffix(".svg"), width=width, height=height)


def add_mesh(fig, mesh, name, color, opacity):
    v = mesh.vertices
    f = mesh.faces
    fig.add_trace(go.Mesh3d(
        x=v[:,0], y=v[:,1], z=v[:,2],
        i=f[:,0], j=f[:,1], k=f[:,2],
        color=color,
        opacity=opacity,
        flatshading=True,
        name=name,
        showscale=False,
    ))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secondaries", required=True)
    ap.add_argument("--nervous-stl", required=True)
    ap.add_argument("--placement-manifest", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mm-per-model-unit", type=float, default=0.1)
    ap.add_argument("--threshold-um", type=float, default=10.0)
    ap.add_argument("--surface-samples", type=int, default=500000)
    ap.add_argument("--max-faces", type=int, default=180000)
    ap.add_argument("--connector-lines", type=int, default=80)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    sec = pd.read_csv(args.secondaries)
    xyz, scale, unit = find_cols(sec)
    pts_mm = sec[list(xyz)].to_numpy(float) * scale

    center_model = compute_center_from_manifest(Path(args.placement_manifest))

    nervous_full = trimesh.load_mesh(Path(args.nervous_stl), force="mesh")
    ref_model = sample_reference_points(nervous_full, args.surface_samples, args.seed)
    ref_mm = (ref_model - center_model[None, :]) * args.mm_per_model_unit

    tree = cKDTree(ref_mm)
    dist_mm, idx = tree.query(pts_mm, k=1, workers=-1)
    nearest_mm = ref_mm[idx]
    dist_um = dist_mm * 1000.0
    near = dist_um <= args.threshold_um

    # Transform nervous mesh for plotting.
    nervous_plot = simplify_for_plot(nervous_full, args.max_faces)
    nervous_plot.vertices = (nervous_plot.vertices - center_model[None, :]) * args.mm_per_model_unit

    # Optional body envelope for spatial context.
    manifest = pd.read_csv(args.placement_manifest)
    body_meshes = []
    for _, r in manifest.iterrows():
        if "WholeBodyEnvelope" in str(r["safe_name"]):
            m = trimesh.load_mesh(Path(r["stl_path"]), force="mesh")
            m.vertices = (m.vertices - center_model[None, :]) * args.mm_per_model_unit
            body_meshes.append(m)

    qc = {
        "n_secondaries": int(len(sec)),
        "threshold_um": args.threshold_um,
        "n_near": int(near.sum()),
        "fraction_near": float(near.mean()) if len(near) else 0.0,
        "distance_um_min": float(np.min(dist_um)),
        "distance_um_p05": float(np.percentile(dist_um, 5)),
        "distance_um_p25": float(np.percentile(dist_um, 25)),
        "distance_um_median": float(np.median(dist_um)),
        "distance_um_p75": float(np.percentile(dist_um, 75)),
        "distance_um_p95": float(np.percentile(dist_um, 95)),
        "distance_um_max": float(np.max(dist_um)),
        "secondary_bounds_mm_min": pts_mm.min(axis=0).tolist(),
        "secondary_bounds_mm_max": pts_mm.max(axis=0).tolist(),
        "nervous_reference_bounds_mm_min": ref_mm.min(axis=0).tolist(),
        "nervous_reference_bounds_mm_max": ref_mm.max(axis=0).tolist(),
        "center_model_units": center_model.tolist(),
        "position_columns": list(xyz),
        "position_input_unit": unit,
        "position_scale_to_mm": scale,
    }

    (outdir / "alignment_qc_summary.json").write_text(json.dumps(qc, indent=2))
    pd.DataFrame({
        "distance_um": dist_um,
        "near": near,
        "region_key": sec["region_key"] if "region_key" in sec.columns else "",
        "ekin_keV": sec["ekin_keV"] if "ekin_keV" in sec.columns else np.nan,
    }).to_csv(outdir / "alignment_qc_distances.csv", index=False)

    print(json.dumps(qc, indent=2))

    # Figure 1: all secondaries colored by distance.
    fig = go.Figure()
    for b in body_meshes:
        add_mesh(fig, b, "Body envelope", "rgba(180,180,180,0.12)", 0.12)
    add_mesh(fig, nervous_plot, "High-resolution nervous anatomy", "rgba(30,80,190,0.25)", 0.25)

    fig.add_trace(go.Scatter3d(
        x=pts_mm[:,0], y=pts_mm[:,1], z=pts_mm[:,2],
        mode="markers",
        marker=dict(
            size=4,
            color=np.minimum(dist_um, 100.0),
            colorscale="Turbo_r",
            colorbar=dict(title="Distance to nervous mesh (µm)"),
            opacity=0.80,
        ),
        name="All secondary electrons",
        text=[f"d={d:.2f} µm" for d in dist_um],
    ))

    fig.update_layout(title="QC: all secondary electrons colored by distance to high-resolution nervous anatomy")
    write(fig, outdir / "qc_all_secondaries_colored_by_distance")

    # Figure 2: near vs far.
    fig = go.Figure()
    for b in body_meshes:
        add_mesh(fig, b, "Body envelope", "rgba(180,180,180,0.10)", 0.10)
    add_mesh(fig, nervous_plot, "High-resolution nervous anatomy", "rgba(30,80,190,0.28)", 0.28)

    far = ~near
    if far.any():
        fig.add_trace(go.Scatter3d(
            x=pts_mm[far,0], y=pts_mm[far,1], z=pts_mm[far,2],
            mode="markers",
            marker=dict(size=3, color="lightgray", opacity=0.35),
            name=f">{args.threshold_um:g} µm from nervous mesh",
        ))
    if near.any():
        fig.add_trace(go.Scatter3d(
            x=pts_mm[near,0], y=pts_mm[near,1], z=pts_mm[near,2],
            mode="markers",
            marker=dict(size=5, color="crimson", opacity=0.85),
            name=f"≤{args.threshold_um:g} µm from nervous mesh",
            text=[f"d={d:.2f} µm" for d in dist_um[near]],
        ))

    # Connector lines for a reproducible subset of near points.
    rng = np.random.default_rng(args.seed)
    near_idx = np.where(near)[0]
    if len(near_idx):
        chosen = rng.choice(near_idx, size=min(args.connector_lines, len(near_idx)), replace=False)
        xs, ys, zs = [], [], []
        for ii in chosen:
            xs += [pts_mm[ii,0], nearest_mm[ii,0], None]
            ys += [pts_mm[ii,1], nearest_mm[ii,1], None]
            zs += [pts_mm[ii,2], nearest_mm[ii,2], None]
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="black", width=2),
            opacity=0.45,
            name="nearest-mask connector lines",
        ))

    fig.update_layout(title=f"QC: high-resolution nervous mask overlap check ({args.threshold_um:g} µm threshold)")
    write(fig, outdir / "qc_near_far_with_nearest_connectors")

    # Figure 3: distance histogram.
    hist = px.histogram(
        pd.DataFrame({"distance_um": dist_um}),
        x="distance_um",
        nbins=80,
        labels={"distance_um": "Distance to high-resolution nervous anatomy (µm)", "count": "Secondary electrons"},
        title="QC: distance distribution to high-resolution nervous anatomy",
    )
    hist.add_vline(x=args.threshold_um, line_dash="dash", line_color="red")
    hist.update_layout(template="plotly_white", font=dict(family="Arial", size=16))
    hist.write_html(outdir / "qc_distance_histogram.html", include_plotlyjs="cdn")
    hist.write_image(outdir / "qc_distance_histogram.png", width=1200, height=700, scale=2)
    hist.write_image(outdir / "qc_distance_histogram.svg", width=1200, height=700)

    print("wrote", outdir)


if __name__ == "__main__":
    main()
