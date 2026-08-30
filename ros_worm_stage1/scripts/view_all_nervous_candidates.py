from pathlib import Path
import os, shutil
import numpy as np
import trimesh
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave

root = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline")
paths = sorted(set(list(root.rglob("*Nerv*.stl")) + list(root.rglob("*nerv*.stl"))))

# Keep the most relevant/non-backup candidates first
preferred = []
for key in [
    "NervousSystem_baked_union.stl",
    "NervousSystem_concat_oriented.stl",
    "NervousSystem_concat.stl",
    "NervousSystem_raw_binary_concat.stl",
    "NervousSystem_baked_union_voxel_0.030.stl",
]:
    preferred += [p for p in paths if p.name == key]
paths = preferred + [p for p in paths if p not in preferred]
paths = paths[:8]

fig = make_subplots(
    rows=len(paths), cols=1,
    specs=[[{"type": "scene"}] for _ in paths],
    subplot_titles=[p.name for p in paths],
    vertical_spacing=0.02,
)

for r, p in enumerate(paths, start=1):
    m = trimesh.load_mesh(p, force="mesh")
    if len(m.faces) > 60000:
        try:
            m = m.simplify_quadric_decimation(face_count=60000)
        except Exception:
            pass

    v = m.vertices
    f = m.faces
    fig.add_trace(
        go.Mesh3d(
            x=v[:,0], y=v[:,1], z=v[:,2],
            i=f[:,0], j=f[:,1], k=f[:,2],
            color="royalblue",
            opacity=0.95,
            flatshading=True,
            name=p.name,
            showscale=False,
            hovertemplate=p.name + "<extra></extra>",
        ),
        row=r, col=1
    )
    fig.update_scenes(aspectmode="data", row=r, col=1)

fig.update_layout(
    template="plotly_white",
    title="Nervous system STL candidates",
    height=max(600, 420 * len(paths)),
    width=1500,
    margin=dict(l=0, r=0, t=80, b=0),
    font=dict(family="Arial", size=14),
)

out = Path("postprocessed_ros_worm/worm_3d/nervous_candidates_comparison.html")
out.parent.mkdir(parents=True, exist_ok=True)
fig.write_html(out, include_plotlyjs="cdn")
print("wrote", out)
print("candidates:")
for p in paths:
    print(" ", p)
