import pandas as pd
import trimesh
from pathlib import Path

base = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/non_nervous_priority_bake")
df = pd.read_csv(base / "debug_core_resolved_flat_simple_body_manifest.csv")

row = df[df["category_guess"] == "DigestiveSystem"].iloc[0]
src = Path(row["stl_path"])
out_stl = base / "resolved_stls" / "DigestiveSystem_resolved_simplified_test.stl"

m = trimesh.load_mesh(src, force="mesh")
print("SRC", src)
print("faces", len(m.faces), "verts", len(m.vertices), "watertight", m.is_watertight, "winding", m.is_winding_consistent, "vol", m.volume)

# Keep largest component if fragments exist.
parts = m.split(only_watertight=False)
print("components", len(parts))
if len(parts) > 1:
    parts = sorted(parts, key=lambda x: len(x.faces), reverse=True)
    # For a system like digestive, do NOT discard components unless tiny.
    # Keep components with at least 1% of largest component faces.
    largest = len(parts[0].faces)
    keep = [x for x in parts if len(x.faces) >= 0.01 * largest]
    print("keeping components", len(keep), "of", len(parts))
    m = trimesh.util.concatenate(keep)

# Version-safe cleanup.
try:
    m.update_faces(m.unique_faces())
except Exception as e:
    print("unique_faces skipped:", e)
try:
    m.update_faces(m.nondegenerate_faces())
except Exception as e:
    print("nondegenerate_faces skipped:", e)

m.remove_unreferenced_vertices()
m.merge_vertices()

try:
    trimesh.repair.fix_normals(m)
except Exception as e:
    print("fix_normals skipped:", e)
try:
    trimesh.repair.fix_winding(m)
except Exception as e:
    print("fix_winding skipped:", e)
try:
    trimesh.repair.fill_holes(m)
except Exception as e:
    print("fill_holes skipped:", e)

# Try decimation if available.
target = min(len(m.faces), 12000)
try:
    m = m.simplify_quadric_decimation(face_count=target)
    print("decimated to", len(m.faces))
except Exception as e:
    print("decimation skipped:", e)

try:
    m.update_faces(m.unique_faces())
    m.update_faces(m.nondegenerate_faces())
except Exception:
    pass
m.remove_unreferenced_vertices()
m.merge_vertices()
trimesh.repair.fix_normals(m)

m.export(out_stl)

test = df.copy()
test.loc[test["category_guess"] == "DigestiveSystem", "stl_path"] = str(out_stl)
out_manifest = base / "debug_simple_body_digestive_simplified_test_manifest.csv"
test.to_csv(out_manifest, index=False)

print("OUT", out_stl)
print("faces", len(m.faces), "verts", len(m.vertices), "watertight", m.is_watertight, "winding", m.is_winding_consistent, "vol", m.volume)
print("manifest", out_manifest)
