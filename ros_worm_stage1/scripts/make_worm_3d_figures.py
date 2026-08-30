#!/usr/bin/env python3
from pathlib import Path
import os, shutil
import numpy as np
import pandas as pd
import trimesh
import plotly.graph_objects as go
import plotly.express as px

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave

ROOT = Path("/home/asunkari/ros-worm/ros_worm_stage1")
MANIFEST = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_plus_nervous_voxel030_manifest.csv")
STATS = ROOT / "postprocessed_ros_worm/publication_plots/plot_table_deposited_energy_fraction_by_source.csv"
OUT = ROOT / "postprocessed_ros_worm/worm_3d"
OUT.mkdir(parents=True, exist_ok=True)

LABEL_FROM_SAFE = {
    "WholeBodyEnvelope": "Residual body envelope",
    "NervousSystem": "Nervous system",
    "BodyWallMuscle": "Body wall muscle",
    "DigestiveSystem": "Digestive system",
    "ReproductiveSystem": "Reproductive system",
    "ExcretorySystem": "Excretory system",
}

COLOR_SCALE = px.colors.sequential.Viridis

def simplify_mesh(mesh, max_faces=45000):
    """
    Visualization-only simplification.
    Never randomly delete faces; that creates fake holes.
    Use quadric decimation if available, otherwise keep the full mesh.
    """
    if len(mesh.faces) <= max_faces:
        return mesh

    try:
        m = mesh.simplify_quadric_decimation(face_count=max_faces)
        m.remove_unreferenced_vertices()
        return m
    except Exception as e:
        print("[WARN] quadric decimation unavailable; keeping full mesh:", repr(e))
        return mesh

def mesh_trace(mesh, name, value=None, color=None, opacity=0.85, colorscale=None, cmin=None, cmax=None, showscale=False):
    v = mesh.vertices
    f = mesh.faces
    kwargs = dict(
        x=v[:,0], y=v[:,1], z=v[:,2],
        i=f[:,0], j=f[:,1], k=f[:,2],
        name=name,
        opacity=opacity,
        flatshading=True,
        hovertemplate=f"{name}<br>x=%{{x:.3f}}<br>y=%{{y:.3f}}<br>z=%{{z:.3f}}<extra></extra>",
    )
    if value is not None:
        kwargs["intensity"] = np.full(len(v), value)
        kwargs["colorscale"] = colorscale or "Viridis"
        kwargs["cmin"] = cmin
        kwargs["cmax"] = cmax
        kwargs["showscale"] = showscale
        kwargs["colorbar"] = dict(title="Deposited energy (%)")
    else:
        kwargs["color"] = color or "lightgray"
        kwargs["showscale"] = False
    return go.Mesh3d(**kwargs)

def write(fig, name):
    fig.update_layout(
        template="plotly_white",
        title=dict(text=name.replace("_", " "), x=0.02, font=dict(size=24)),
        scene=dict(
            xaxis_title="x (model units)",
            yaxis_title="y (model units)",
            zaxis_title="z (model units)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.7, y=-2.2, z=1.1)),
        ),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=0, r=0, t=60, b=0),
        font=dict(family="Arial", size=15),
    )
    fig.write_html(str(OUT / f"{name}.html"), include_plotlyjs="cdn")
    fig.write_image(str(OUT / f"{name}.png"), width=1600, height=950, scale=2)
    fig.write_image(str(OUT / f"{name}.svg"), width=1600, height=950)

manifest = pd.read_csv(MANIFEST)
stats = pd.read_csv(STATS)
stats["percent"] = 100.0 * stats["fraction_of_deposited_energy"]

meshes = {}
for _, row in manifest.iterrows():
    safe = row["safe_name"]
    label = LABEL_FROM_SAFE.get(safe, safe)
    p = Path(row["stl_path"])
    if not p.exists():
        print("[WARN] missing STL", p)
        continue
    m = trimesh.load_mesh(p, force="mesh")
    m = simplify_mesh(m, max_faces=45000 if safe != "WholeBodyEnvelope" else 30000)
    meshes[label] = m
    print("[MESH]", label, "faces", len(m.faces), "verts", len(m.vertices))

for source in ["Focused beam", "Diffuse field"]:
    sstats = stats[stats["source_geometry"] == source].copy()
    val = dict(zip(sstats["region_label"], sstats["percent"]))
    vmax_all = max(val.values())
    target_vals = [v for k, v in val.items() if k != "Residual body envelope"]
    vmax_target = max(target_vals) if target_vals else vmax_all

    # Body included, body transparent, inner compartments colored.
    traces = []
    for label, mesh in meshes.items():
        if label == "Residual body envelope":
            traces.append(mesh_trace(mesh, label, color="rgba(180,180,180,0.35)", opacity=0.18))
        else:
            traces.append(mesh_trace(
                mesh, label, value=val.get(label, 0.0),
                opacity=0.88, colorscale="Viridis", cmin=0, cmax=max(vmax_target, 1e-6),
                showscale=(len(traces) == 1)
            ))
    fig = go.Figure(traces)
    write(fig, f"worm_3d_{source.lower().replace(' ','_')}_transparent_body_colored_targets")

    # Target-only view.
    traces = []
    first = True
    for label, mesh in meshes.items():
        if label == "Residual body envelope":
            continue
        traces.append(mesh_trace(
            mesh, label, value=val.get(label, 0.0),
            opacity=0.95, colorscale="Viridis", cmin=0, cmax=max(vmax_target, 1e-6),
            showscale=first
        ))
        first = False
    fig = go.Figure(traces)
    write(fig, f"worm_3d_{source.lower().replace(' ','_')}_targets_only")

    # All compartments colored, including body, with body low opacity.
    traces = []
    first = True
    for label, mesh in meshes.items():
        opacity = 0.25 if label == "Residual body envelope" else 0.9
        traces.append(mesh_trace(
            mesh, label, value=val.get(label, 0.0),
            opacity=opacity, colorscale="Viridis", cmin=0, cmax=max(vmax_all, 1e-6),
            showscale=first
        ))
        first = False
    fig = go.Figure(traces)
    write(fig, f"worm_3d_{source.lower().replace(' ','_')}_all_compartments_colored")

print("[OK] wrote 3D figures to", OUT)
