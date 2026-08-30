from pathlib import Path
import pandas as pd
import trimesh
import numpy as np

manifest = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")
df = pd.read_csv(manifest)

rows = df[df["category_guess"] == "NervousSystem"].copy()
meshes = []

def clean_member(m):
    m = m.copy()
    m.remove_unreferenced_vertices()
    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0)
    if keep.sum() != len(m.faces):
        m.update_faces(keep)
        m.remove_unreferenced_vertices()
    # Important: process each member only, not the final combined mesh.
    m.process(validate=True)
    if m.volume < 0:
        m.invert()
    return m

print("nervous member count:", len(rows))

for _, r in rows.iterrows():
    m = trimesh.load_mesh(r["stl_path"], force="mesh", process=True)
    m = clean_member(m)
    if not m.is_watertight:
        print("[WARN member not watertight]", r["object_name"], r["stl_path"])
    meshes.append(m)

# Concatenate only. Do NOT global process/validate after this.
c = trimesh.util.concatenate(meshes)
c.remove_unreferenced_vertices()

out = outdir / "NervousSystem_concat_no_global_process.stl"
c.export(out)

print("wrote:", out)
print("watertight:", c.is_watertight)
print("components:", len(c.split(only_watertight=False)))
print("faces:", len(c.faces))
print("volume:", c.volume)
print("bounds:", c.bounds)

# Non-manifold edge diagnostic.
edges_sorted = np.sort(c.edges, axis=1)
edges_unique, counts = np.unique(edges_sorted, axis=0, return_counts=True)
bad = edges_unique[counts != 2]
print("unique edges:", len(edges_unique))
print("bad edge count:", len(bad))
print("edge count distribution:")
vals, cnts = np.unique(counts, return_counts=True)
for v, n in zip(vals, cnts):
    print("  count", int(v), ":", int(n))
