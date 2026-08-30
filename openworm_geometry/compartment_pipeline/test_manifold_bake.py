from pathlib import Path
import pandas as pd
import trimesh
import numpy as np
import sys

manifest = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")
outdir.mkdir(parents=True, exist_ok=True)

category = sys.argv[1] if len(sys.argv) > 1 else "ExcretorySystem"

df = pd.read_csv(manifest)
rows = df[df["category_guess"] == category].copy()

print("[bake] category:", category)
print("[bake] source objects:", len(rows))

def clean_mesh(m):
    # Works across newer Trimesh versions.
    m = m.copy()
    m.remove_unreferenced_vertices()

    # Drop explicitly zero-area / invalid faces without deprecated methods.
    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0.0)
    if keep.sum() != len(m.faces):
        print("[clean] dropping degenerate faces:", len(m.faces) - int(keep.sum()))
        m.update_faces(keep)
        m.remove_unreferenced_vertices()

    m.process(validate=True)

    if m.volume < 0:
        m.invert()

    return m

meshes = []
for _, r in rows.iterrows():
    p = Path(r["stl_path"])
    m = trimesh.load_mesh(p, force="mesh", process=True)
    m = clean_mesh(m)

    meshes.append(m)
    print(
        "[load]",
        r["object_name"],
        "faces=", len(m.faces),
        "watertight=", m.is_watertight,
        "vol=", m.volume,
    )

print("[bake] union starting...")

# trimesh will use manifold3d if installed.
try:
    u = trimesh.boolean.union(meshes, engine="manifold", check_volume=False)
except TypeError:
    # Fallback for older/different Trimesh signatures.
    u = trimesh.boolean.union(meshes, engine="manifold")

if isinstance(u, list):
    print("[bake] union returned list; concatenating")
    u = trimesh.util.concatenate(u)

u = clean_mesh(u)

out = outdir / f"{category}_baked_union.stl"
u.export(out)

print("[bake] wrote:", out)
print("[bake] watertight:", u.is_watertight)
print("[bake] components:", len(u.split(only_watertight=False)))
print("[bake] faces:", len(u.faces))
print("[bake] volume:", u.volume)
print("[bake] bounds:", u.bounds)
