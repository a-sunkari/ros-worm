import trimesh
from pathlib import Path
import pandas as pd
import numpy as np

rows = []
for p in sorted(Path(".").rglob("*")):
    if p.suffix.lower() not in [".stl", ".obj", ".ply"]:
        continue
    try:
        m = trimesh.load_mesh(p, force="mesh")
        if not isinstance(m, trimesh.Trimesh):
            rows.append({"file": str(p), "note": f"not Trimesh: {type(m)}"})
            continue

        span = m.bounds[1] - m.bounds[0]
        areas = m.area_faces if len(m.faces) else np.array([])
        edges = m.edges_unique_length if len(m.faces) else np.array([])

        rows.append({
            "file": str(p),
            "faces": len(m.faces),
            "verts": len(m.vertices),
            "watertight": m.is_watertight,
            "winding": m.is_winding_consistent,
            "euler": m.euler_number,
            "components": len(m.split(only_watertight=False)),
            "volume": m.volume,
            "area": m.area,
            "span_x": span[0],
            "span_y": span[1],
            "span_z": span[2],
            "min_face_area": float(areas.min()) if len(areas) else None,
            "p01_face_area": float(np.percentile(areas, 1)) if len(areas) else None,
            "min_edge": float(edges.min()) if len(edges) else None,
            "p01_edge": float(np.percentile(edges, 1)) if len(edges) else None,
        })
    except Exception as e:
        rows.append({"file": str(p), "error": repr(e)})

df = pd.DataFrame(rows)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 260)
print(df.to_string(index=False))
df.to_csv("wu_mesh_diagnostics.csv", index=False)
print("\nwrote wu_mesh_diagnostics.csv")
