from pathlib import Path
import pandas as pd
import trimesh
import numpy as np

manifest = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(manifest)

targets = ["HypodermisSeam", "NervousSystem"]

def clean(m):
    m = m.copy()
    m.remove_unreferenced_vertices()
    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0)
    if keep.sum() != len(m.faces):
        m.update_faces(keep)
        m.remove_unreferenced_vertices()
    m.process(validate=True)
    if m.volume < 0:
        m.invert()
    return m

for cat in targets:
    rows = df[df["category_guess"] == cat].copy()
    meshes = []

    print("\n=== concat", cat, "===")
    for _, r in rows.iterrows():
        m = trimesh.load_mesh(r["stl_path"], force="mesh", process=True)
        m = clean(m)
        meshes.append(m)
        print("[member]", r["object_name"], "watertight=", m.is_watertight, "faces=", len(m.faces), "vol=", m.volume)

    c = trimesh.util.concatenate(meshes)
    c = clean(c)

    out = outdir / f"{cat}_concat.stl"
    c.export(out)

    print("[concat] wrote:", out)
    print("[concat] watertight:", c.is_watertight)
    print("[concat] components:", len(c.split(only_watertight=False)))
    print("[concat] faces:", len(c.faces))
    print("[concat] volume:", c.volume)
    print("[concat] bounds:", c.bounds)
