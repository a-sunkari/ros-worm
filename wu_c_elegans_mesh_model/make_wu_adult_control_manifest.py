import pandas as pd
import trimesh
from pathlib import Path

rows_in = [
    (
        "WuBody",
        "WholeBodyEnvelope",
        "whole_body_parent",
        Path("/home/asunkari/ros-worm/wu_c_elegans_mesh_model/split_adult_stls/Reproductive_system.stl"),
    ),
    (
        "WuDigestive",
        "DigestiveSystem",
        "DigestiveSystem",
        Path("/home/asunkari/ros-worm/wu_c_elegans_mesh_model/split_adult_stls/Reproductive_system_1.stl"),
    ),
    (
        "WuReproductive",
        "ReproductiveSystem",
        "ReproductiveSystem",
        Path("/home/asunkari/ros-worm/wu_c_elegans_mesh_model/split_adult_stls/Reproductive_system_2.stl"),
    ),
]

rows = []

for object_name, safe_name, category_guess, p in rows_in:
    if not p.exists():
        raise FileNotFoundError(f"Missing STL: {p}")

    m = trimesh.load_mesh(p, force="mesh")
    b = m.bounds
    span = b[1] - b[0]

    rows.append({
        "object_name": object_name,
        "safe_name": safe_name,
        "category_guess": category_guess,
        "stl_path": str(p.resolve()),
        "raw_triangles": len(m.faces),
        "exported_triangles": len(m.faces),
        "skipped_degenerate": 0,
        "min_x": float(b[0, 0]),
        "min_y": float(b[0, 1]),
        "min_z": float(b[0, 2]),
        "max_x": float(b[1, 0]),
        "max_y": float(b[1, 1]),
        "max_z": float(b[1, 2]),
        "span_x": float(span[0]),
        "span_y": float(span[1]),
        "span_z": float(span[2]),
        "repair_used_meshfix": False,
        "repair_watertight_after": bool(m.is_watertight),
        "repair_winding_after": bool(m.is_winding_consistent),
        "repair_faces_after": len(m.faces),
    })

df = pd.DataFrame(rows)
out = Path("/home/asunkari/ros-worm/wu_c_elegans_mesh_model/wu_adult_control_manifest.csv")
df.to_csv(out, index=False)

print("WROTE:", out)
print("COLUMNS:", list(df.columns))
print(df.to_string(index=False))
