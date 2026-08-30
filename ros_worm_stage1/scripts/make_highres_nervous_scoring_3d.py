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


def compute_center(manifest: Path):
    df = pd.read_csv(manifest)
    mins, maxs = [], []
    for p in df["stl_path"]:
        m = trimesh.load_mesh(Path(p), force="mesh")
        mins.append(m.bounds[0])
        maxs.append(m.bounds[1])
    return 0.5 * (np.min(np.vstack(mins), axis=0) + np.max(np.vstack(maxs), axis=0))


def find_cols(df):
    candidates = [
        (("x_mm", "y_mm", "z_mm"), 1.0, "mm"),
        (("pos_x_mm", "pos_y_mm", "pos_z_mm"), 1.0, "mm"),
        (("x_um", "y_um", "z_um"), 1.0e-3, "um"),
        (("pos_x_um", "pos_y_um", "pos_z_um"), 1.0e-3, "um"),
        (("x", "y", "z"), 1.0, "assumed_mm"),
    ]
    for xyz, scale, unit in candidates:
        if all(c in df.columns for c in xyz):
            break
    else:
        raise SystemExit("No xyz columns found. Columns:\n" + "\n".join(df.columns.astype(str)))

    for e in ["ekin_keV", "energy_keV", "e_keV"]:
        if e in df.columns:
            return xyz, scale, unit, e
    raise SystemExit("No energy column found")


def simplify_for_plot(mesh, max_faces):
    if len(mesh.faces) <= max_faces:
        return mesh
    try:
        return mesh.simplify_quadric_decimation(face_count=max_faces)
    except Exception:
        # If decimation unavailable, take every nth face for plotting only, but do not use this for scoring.
        n = max(1, len(mesh.faces) // max_faces)
        m = mesh.copy()
        m.update_faces(np.arange(0, len(m.faces), n))
        m.remove_unreferenced_vertices()
        return m


def write(fig, out_base: Path, w=1600, h=950):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=15),
        title=dict(x=0.02, xanchor="left", font=dict(size=24)),
        scene=dict(
            xaxis_title="x (mm)",
            yaxis_title="y (mm)",
            zaxis_title="z (mm)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=-2.1, z=1.0)),
        ),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    fig.write_html(out_base.with_suffix(".html"), include_plotlyjs="cdn")
    fig.write_image(out_base.with_suffix(".png"), width=w, height=h, scale=2)
    fig.write_image(out_base.with_suffix(".svg"), width=w, height=h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nervous-stl", required=True)
    ap.add_argument("--placement-manifest", required=True)
    ap.add_argument("--scored-secondaries", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mm-per-model-unit", type=float, default=0.1)
    ap.add_argument("--threshold-um", type=float, default=10)
    ap.add_argument("--density-radius-um", type=float, default=25)
    ap.add_argument("--max-faces", type=int, default=180000)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    center = compute_center(Path(args.placement_manifest))

    mesh_full = trimesh.load_mesh(Path(args.nervous_stl), force="mesh")
    mesh = simplify_for_plot(mesh_full, args.max_faces)

    verts_mm = (np.asarray(mesh.vertices, float) - center[None, :]) * args.mm_per_model_unit
    faces = mesh.faces

    df = pd.read_csv(args.scored_secondaries)
    xyz, position_scale_to_mm, position_unit, ecol = find_cols(df)

    near_col = "near_highres_nervous"
    if near_col in df.columns:
        near = df[df[near_col]].copy()
    else:
        near = df[df["distance_to_highres_nervous_um"] <= args.threshold_um].copy()

    pts = near[list(xyz)].to_numpy(float) * position_scale_to_mm if len(near) else np.zeros((0,3))

    # Figure 1: anatomy + electron source points
    fig = go.Figure()

    fig.add_trace(go.Mesh3d(
        x=verts_mm[:,0], y=verts_mm[:,1], z=verts_mm[:,2],
        i=faces[:,0], j=faces[:,1], k=faces[:,2],
        color="rgba(40,90,200,0.35)",
        opacity=0.35,
        flatshading=True,
        name="High-resolution nervous anatomy",
        showscale=False,
    ))

    if len(near):
        fig.add_trace(go.Scatter3d(
            x=pts[:,0], y=pts[:,1], z=pts[:,2],
            mode="markers",
            marker=dict(
                size=4,
                color=near[ecol],
                colorscale="Inferno",
                colorbar=dict(title="Electron energy (keV)"),
                opacity=0.85,
            ),
            name=f"Secondary electrons within {args.threshold_um:g} µm",
            text=[f"{e:.3g} keV<br>{d:.2f} µm" for e, d in zip(near[ecol], near["distance_to_highres_nervous_um"])],
        ))

    fig.update_layout(title=f"High-resolution nervous anatomy with nearby secondary electrons ({args.threshold_um:g} µm mask)")
    write(fig, outdir / "highres_nervous_nearby_secondary_electrons")

    # Figure 2: nervous mesh colored by local source-term density.
    if len(near):
        tree = cKDTree(pts)
        radius_mm = args.density_radius_um * 1e-3
        counts = np.array([len(x) for x in tree.query_ball_point(verts_mm, r=radius_mm)], dtype=float)
        # Avoid one crazy spike dominating.
        cmax = np.percentile(counts[counts > 0], 98) if np.any(counts > 0) else 1.0
    else:
        counts = np.zeros(len(verts_mm))
        cmax = 1.0

    fig = go.Figure(go.Mesh3d(
        x=verts_mm[:,0], y=verts_mm[:,1], z=verts_mm[:,2],
        i=faces[:,0], j=faces[:,1], k=faces[:,2],
        intensity=counts,
        colorscale="Viridis",
        cmin=0,
        cmax=max(cmax, 1.0),
        colorbar=dict(title=f"Nearby e⁻ count<br>within {args.density_radius_um:g} µm"),
        opacity=0.95,
        flatshading=True,
        name="High-resolution nervous anatomy",
    ))

    fig.update_layout(title=f"High-resolution nervous anatomy colored by local secondary-electron proximity density")
    write(fig, outdir / "highres_nervous_colored_by_secondary_density")

    summary = {
        "nervous_stl": args.nervous_stl,
        "scored_secondaries": args.scored_secondaries,
        "threshold_um": args.threshold_um,
        "density_radius_um": args.density_radius_um,
        "n_near_secondaries": int(len(near)),
        "n_plot_vertices": int(len(verts_mm)),
        "n_plot_faces": int(len(faces)),
    }
    (outdir / "highres_nervous_3d_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print("wrote", outdir)


if __name__ == "__main__":
    main()
