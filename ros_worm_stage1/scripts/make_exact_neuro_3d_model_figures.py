#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import os, shutil

import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree
import plotly.graph_objects as go

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave


COLORS = {
    "WholeBodyEnvelope": "rgba(180,180,180,0.16)",
    "BodyWallMuscle": "rgba(196,78,82,0.62)",
    "DigestiveSystem": "rgba(85,168,104,0.70)",
    "ReproductiveSystem": "rgba(129,114,178,0.70)",
    "ExcretorySystem": "rgba(204,185,116,0.85)",
    "NervousSystem": "rgba(30,80,190,0.62)",
}


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
    except Exception as e:
        print("[WARN] decimation failed:", repr(e))
        return mesh


def transform_mesh(mesh, center, scale):
    m = mesh.copy()
    m.vertices = (m.vertices - center[None, :]) * scale
    return m


def add_mesh(fig, mesh, name, color, opacity=None):
    v = mesh.vertices
    f = mesh.faces
    fig.add_trace(go.Mesh3d(
        x=v[:, 0], y=v[:, 1], z=v[:, 2],
        i=f[:, 0], j=f[:, 1], k=f[:, 2],
        name=name,
        color=color,
        opacity=opacity if opacity is not None else 1.0,
        flatshading=True,
        showscale=False,
    ))


def write(fig, outbase, width=1700, height=950):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=15),
        title=dict(x=0.02, xanchor="left", font=dict(size=24)),
        scene=dict(
            xaxis_title="x (mm)",
            yaxis_title="y (mm)",
            zaxis_title="z (mm)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.55, y=-2.15, z=1.05)),
        ),
        margin=dict(l=0, r=0, t=70, b=0),
        legend=dict(x=0.01, y=0.99),
    )
    outbase.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(outbase.with_suffix(".html"), include_plotlyjs="cdn")
    fig.write_image(outbase.with_suffix(".png"), width=width, height=height, scale=2)
    fig.write_image(outbase.with_suffix(".svg"), width=width, height=height)


def make_geometry_figures(manifest, nervous_stl, outdir, scale, max_faces):
    center = compute_center(manifest)
    df = pd.read_csv(manifest)

    # Figure 1: physical transport geometry only.
    fig = go.Figure()
    for _, row in df.iterrows():
        safe = str(row["safe_name"])
        mesh = trimesh.load_mesh(Path(row["stl_path"]), force="mesh")
        mesh = simplify(mesh, max_faces)
        mesh = transform_mesh(mesh, center, scale)
        add_mesh(fig, mesh, safe, COLORS.get(safe, "rgba(80,80,80,0.6)"))
    fig.update_layout(title="ROS-Worm physical transport geometry: no physical nervous volume")
    write(fig, outdir / "geometry_physical_transport_compartments_no_nervous")

    # Figure 2: high-res nervous overlay with transparent body.
    fig = go.Figure()
    for _, row in df.iterrows():
        safe = str(row["safe_name"])
        mesh = trimesh.load_mesh(Path(row["stl_path"]), force="mesh")
        mesh = simplify(mesh, max_faces if safe != "WholeBodyEnvelope" else min(max_faces, 50000))
        mesh = transform_mesh(mesh, center, scale)
        color = COLORS.get(safe, "rgba(80,80,80,0.5)")
        add_mesh(fig, mesh, safe, color)

    nervous = trimesh.load_mesh(nervous_stl, force="mesh")
    nervous = simplify(nervous, max_faces * 2)
    nervous = transform_mesh(nervous, center, scale)
    add_mesh(fig, nervous, "High-resolution nervous anatomy scoring mask", COLORS["NervousSystem"])
    fig.update_layout(title="High-resolution nervous anatomy overlaid on physical transport geometry")
    write(fig, outdir / "geometry_highres_nervous_overlay")


def make_exact_neuro_figures(run, manifest, nervous_stl, outdir, scale, max_faces, threshold_um, density_radius_um):
    center = compute_center(manifest)
    scored_f = run / "highres_nervous_exact_surface_scoring" / "secondary_electrons_with_exact_nervous_surface_distance.csv"
    if not scored_f.exists():
        raise SystemExit(f"Missing exact-scored secondary file: {scored_f}")

    sec = pd.read_csv(scored_f)
    xyz = ("x_um", "y_um", "z_um") if "x_um" in sec.columns else ("x_mm", "y_mm", "z_mm")
    pos_scale = 1e-3 if xyz[0].endswith("_um") else 1.0
    pts = sec[list(xyz)].to_numpy(float) * pos_scale
    dist = sec["distance_to_highres_nervous_surface_um"].to_numpy(float)
    near = dist <= threshold_um
    closest = sec[["closest_nervous_x_mm", "closest_nervous_y_mm", "closest_nervous_z_mm"]].to_numpy(float)

    nervous = trimesh.load_mesh(nervous_stl, force="mesh")
    nervous = simplify(nervous, max_faces * 2)
    nervous = transform_mesh(nervous, center, scale)

    # Figure 3: near/far points + exact closest connectors.
    fig = go.Figure()
    add_mesh(fig, nervous, "High-resolution nervous anatomy", "rgba(30,80,190,0.28)")

    far = ~near
    if far.any():
        fig.add_trace(go.Scatter3d(
            x=pts[far,0], y=pts[far,1], z=pts[far,2],
            mode="markers",
            marker=dict(size=3, color="lightgray", opacity=0.25),
            name=f">{threshold_um:g} µm from nervous surface",
        ))

    if near.any():
        fig.add_trace(go.Scatter3d(
            x=pts[near,0], y=pts[near,1], z=pts[near,2],
            mode="markers",
            marker=dict(size=5, color="crimson", opacity=0.9),
            name=f"≤{threshold_um:g} µm near-neural shell",
            text=[f"d={d:.2f} µm" for d in dist[near]],
        ))

    # connector lines to exact closest points, limited for readability
    near_idx = np.where(near)[0]
    rng = np.random.default_rng(12345)
    if len(near_idx):
        chosen = rng.choice(near_idx, size=min(120, len(near_idx)), replace=False)
        xs, ys, zs = [], [], []
        for ii in chosen:
            xs += [pts[ii,0], closest[ii,0], None]
            ys += [pts[ii,1], closest[ii,1], None]
            zs += [pts[ii,2], closest[ii,2], None]
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="black", width=2),
            opacity=0.45,
            name="exact closest-surface connectors",
        ))

    fig.update_layout(title=f"Exact high-resolution nervous-surface scoring: {threshold_um:g} µm near-neural shell")
    write(fig, outdir / f"exact_neuro_surface_scoring_{threshold_um:g}um_near_far_connectors")

    # Figure 4: nervous mesh colored by local density of near-neural secondaries.
    v = nervous.vertices
    if near.any():
        tree = cKDTree(closest[near])
        radius_mm = density_radius_um * 1e-3
        counts = np.array([len(x) for x in tree.query_ball_point(v, r=radius_mm)], dtype=float)
        cmax = np.percentile(counts[counts > 0], 98) if np.any(counts > 0) else 1
    else:
        counts = np.zeros(len(v))
        cmax = 1

    f = nervous.faces
    fig = go.Figure(go.Mesh3d(
        x=v[:,0], y=v[:,1], z=v[:,2],
        i=f[:,0], j=f[:,1], k=f[:,2],
        intensity=counts,
        colorscale="Viridis",
        cmin=0,
        cmax=max(cmax, 1),
        colorbar=dict(title=f"Nearby e⁻ count<br>within {density_radius_um:g} µm"),
        opacity=0.95,
        flatshading=True,
        name="High-resolution nervous anatomy",
    ))
    fig.update_layout(title=f"High-resolution nervous anatomy colored by local near-neural secondary-electron density")
    write(fig, outdir / "exact_neuro_highres_nervous_colored_by_local_secondary_density")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--nervous-stl", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mm-per-model-unit", type=float, default=0.1)
    ap.add_argument("--max-faces", type=int, default=180000)
    ap.add_argument("--threshold-um", type=float, default=5)
    ap.add_argument("--density-radius-um", type=float, default=25)
    args = ap.parse_args()

    run = Path(args.run)
    manifest = Path(args.manifest)
    nervous_stl = Path(args.nervous_stl)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    make_geometry_figures(manifest, nervous_stl, outdir, args.mm_per_model_unit, args.max_faces)
    make_exact_neuro_figures(run, manifest, nervous_stl, outdir, args.mm_per_model_unit, args.max_faces, args.threshold_um, args.density_radius_um)

    print("[OK] wrote 3D figures to", outdir)


if __name__ == "__main__":
    main()
