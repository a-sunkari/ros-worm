import trimesh
import pandas as pd
from pathlib import Path

# TODO: replace these after inspecting wu_mesh_diagnostics.txt
BODY = Path("/ABS/PATH/TO/BODY.stl")
DIGESTIVE = Path("/ABS/PATH/TO/DIGESTIVE.stl")
REPRODUCTIVE = Path("/ABS/PATH/TO/REPRODUCTIVE.stl")

rows_in = [
    ("WuBody", "WholeBodyEnvelope", "whole_body_parent", BODY),
    ("WuDigestive", "DigestiveSystem", "DigestiveSystem", DIGESTIVE),
    ("WuReproductive", "ReproductiveSystem", "ReproductiveSystem", REPRODUCTIVE),
]

rows = []
for object_name, safe_name, category_guess, p in rows_in:
    p = Path(p)
    if not p.exists():
        raise FileNotFoundError(p)

    m = trimesh.load_mesh(p, force="mesh")
    b = m.bounds

    rows.append({
        "object_name": object_name,
        "safe_name": safe_name,
        "category_guess": category_guess,
        "stl_path": str(p.resolve()),
        "raw_triangles": len(m.faces),
        "exported_triangles": len(m.faces),
        "skipped_degenerate": 0,
        "min_x": b[0,0],
        "min_y": b[0,1],
        "min_z": b[0,2],
        "max_x": b[1,0],
        "max_y": b[1,1],
        "max_z": b[1,2],
        "span_x": b[1,0] - b[0,0],
        "span_y": b[1,1] - b[0,1],
        "span_z": b[1,2] - b[0,2],
        "repair_used_meshfix": False,
        "repair_watertight_after": m.is_watertight,
        "repair_winding_after": m.is_winding_consistent,
        "repair_faces_after": len(m.faces),
    })

df = pd.DataFrame(rows)
out = Path("wu_adult_control_manifest.csv")
df.to_csv(out, index=False)

print("wrote", out.resolve())
print(df.to_string(index=False))
