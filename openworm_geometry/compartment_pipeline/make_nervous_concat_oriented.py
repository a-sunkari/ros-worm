from pathlib import Path
import pandas as pd
import trimesh
import numpy as np

manifest = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")
df = pd.read_csv(manifest)

rows = df[df["category_guess"] == "NervousSystem"].copy()
meshes = []

print("nervous member count:", len(rows))

def clean_orient_member(m, name):
    m = m.copy()
    m.remove_unreferenced_vertices()

    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0)
    if keep.sum() != len(m.faces):
        print("[clean]", name, "dropping degenerate faces:", len(m.faces) - int(keep.sum()))
        m.update_faces(keep)
        m.remove_unreferenced_vertices()

    # Do member-level repair only. Do NOT globally process final concat.
    try:
        trimesh.repair.fix_winding(m)
    except Exception as e:
        print("[WARN]", name, "fix_winding:", repr(e))

    try:
        trimesh.repair.fix_inversion(m)
    except Exception as e:
        print("[WARN]", name, "fix_inversion:", repr(e))

    try:
        trimesh.repair.fix_normals(m)
    except Exception as e:
        print("[WARN]", name, "fix_normals:", repr(e))

    m.process(validate=True)

    if m.volume < 0:
        m.invert()

    return m

bad_members = []

for _, r in rows.iterrows():
    name = r["object_name"]
    m = trimesh.load_mesh(r["stl_path"], force="mesh", process=True)
    m = clean_orient_member(m, name)

    if not m.is_watertight:
        bad_members.append((name, "not_watertight"))

    if hasattr(m, "is_winding_consistent") and not m.is_winding_consistent:
        bad_members.append((name, "bad_winding"))

    meshes.append(m)

c = trimesh.util.concatenate(meshes)
c.remove_unreferenced_vertices()

# No global process(validate=True), no global normal repair.
out = outdir / "NervousSystem_concat_oriented.stl"
c.export(out)

edges_sorted = np.sort(c.edges, axis=1)
edges_unique, counts = np.unique(edges_sorted, axis=0, return_counts=True)
bad_edges = edges_unique[counts != 2]

print("wrote:", out)
print("watertight:", c.is_watertight)
print("components:", len(c.split(only_watertight=False)))
print("faces:", len(c.faces))
print("volume:", c.volume)
print("bounds:", c.bounds)
print("bad member count:", len(bad_members))
print("bad members:", bad_members[:50])
print("unique edges:", len(edges_unique))
print("bad edge count:", len(bad_edges))
vals, cnts = np.unique(counts, return_counts=True)
print("edge count distribution:")
for v, n in zip(vals, cnts):
    print("  count", int(v), ":", int(n))
