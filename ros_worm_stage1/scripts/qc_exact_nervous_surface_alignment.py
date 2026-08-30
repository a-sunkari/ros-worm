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

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave


def find_xyz(df):
    if all(c in df.columns for c in ["x_um", "y_um", "z_um"]):
        return ("x_um", "y_um", "z_um"), 1e-3
    if all(c in df.columns for c in ["x_mm", "y_mm", "z_mm"]):
        return ("x_mm", "y_mm", "z_mm"), 1.0
    raise SystemExit("No xyz columns")


def compute_center(manifest):
    df = pd.read_csv(manifest)
    mins, maxs = [], []
    for p in df["stl_path"]:
        m = trimesh.load_mesh(Path(p), force="mesh")
        mins.append(m.bounds[0])
        maxs.append(m.bounds[1])
    return 0.5 * (np.min(np.vstack(mins), axis=0) + np.max(np.vstack(maxs), axis=0))


def simplify(mesh, max_faces):
    if len(mesh.faces) <= max_faces:
        return mesh
    try:
        m = mesh.simplify_quadric_decimation(face_count=max_faces)
        m.remove_unreferenced_vertices()
        return m
    except Exception:
        return mesh


def write(fig, out_base):
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
    fig.write_image(out_base.with_suffix(".png"), width=1700, height=950, scale=2)
    fig.write_image(out_base.with_suffix(".svg"), width=1700, height=950)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exact-scored-secondaries", required=True)
    ap.add_argument("--nervous-stl", required=True)
    ap.add_argument("--placement-manifest", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mm-per-model-unit", type=float, default=0.1)
    ap.add_argument("--threshold-um", type=float, default=5)
    ap.add_argument("--max-faces", type=int, default=180000)
    ap.add_argument("--connector-lines", type=int, default=120)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.exact_scored_secondaries)
    xyz, scale = find_xyz(df)
    pts_mm = df[list(xyz)].to_numpy(float) * scale

    dist_um = df["distance_to_highres_nervous_surface_um"].to_numpy(float)
    closest_mm = df[["closest_nervous_x_mm", "closest_nervous_y_mm", "closest_nervous_z_mm"]].to_numpy(float)
    near = dist_um <= args.threshold_um

    center = compute_center(Path(args.placement_manifest))
    nervous = trimesh.load_mesh(Path(args.nervous_stl), force="mesh")
    nervous.vertices = (nervous.vertices - center[None, :]) * args.mm_per_model_unit
    nervous = simplify(nervous, args.max_faces)

    fig = go.Figure()

    v = nervous.vertices
    f = nervous.faces
    fig.add_trace(go.Mesh3d(
        x=v[:,0], y=v[:,1], z=v[:,2],
        i=f[:,0], j=f[:,1], k=f[:,2],
        color="rgba(30,80,190,0.25)",
        opacity=0.25,
        flatshading=True,
        name="High-resolution nervous surface",
        showscale=False,
    ))

    far = ~near
    if far.any():
        fig.add_trace(go.Scatter3d(
            x=pts_mm[far,0], y=pts_mm[far,1], z=pts_mm[far,2],
            mode="markers",
            marker=dict(size=3, color="lightgray", opacity=0.25),
            name=f">{args.threshold_um:g} µm from nervous surface",
        ))

    if near.any():
        fig.add_trace(go.Scatter3d(
            x=pts_mm[near,0], y=pts_mm[near,1], z=pts_mm[near,2],
            mode="markers",
            marker=dict(size=5, color="crimson", opacity=0.9),
            name=f"≤{args.threshold_um:g} µm from nervous surface",
            text=[f"d={d:.2f} µm" for d in dist_um[near]],
        ))

    rng = np.random.default_rng(args.seed)
    near_idx = np.where(near)[0]
    if len(near_idx):
        chosen = rng.choice(near_idx, size=min(args.connector_lines, len(near_idx)), replace=False)
        xs, ys, zs = [], [], []
        for ii in chosen:
            xs += [pts_mm[ii,0], closest_mm[ii,0], None]
            ys += [pts_mm[ii,1], closest_mm[ii,1], None]
            zs += [pts_mm[ii,2], closest_mm[ii,2], None]
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="black", width=2),
            opacity=0.5,
            name="exact closest-surface connector lines",
        ))

    fig.update_layout(title=f"Exact surface-distance QC for high-resolution nervous anatomy ({args.threshold_um:g} µm shell)")
    write(fig, outdir / "qc_exact_surface_near_far_connectors")

    hist = px.histogram(
        pd.DataFrame({"distance_um": dist_um}),
        x="distance_um",
        nbins=90,
        title="Exact distance to high-resolution nervous surface",
        labels={"distance_um": "Exact distance to nervous surface (µm)", "count": "Secondary electrons"},
    )
    hist.add_vline(x=args.threshold_um, line_dash="dash", line_color="red")
    hist.update_layout(template="plotly_white", font=dict(family="Arial", size=16))
    hist.write_html(outdir / "qc_exact_surface_distance_histogram.html", include_plotlyjs="cdn")
    hist.write_image(outdir / "qc_exact_surface_distance_histogram.png", width=1200, height=700, scale=2)
    hist.write_image(outdir / "qc_exact_surface_distance_histogram.svg", width=1200, height=700)

    summary = {
        "threshold_um": args.threshold_um,
        "n_secondaries": int(len(df)),
        "n_near": int(near.sum()),
        "fraction_near": float(near.mean()) if len(df) else 0,
        "distance_um_median": float(np.median(dist_um)),
        "distance_um_p05": float(np.percentile(dist_um, 5)),
        "distance_um_p95": float(np.percentile(dist_um, 95)),
    }
    (outdir / "qc_exact_surface_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
