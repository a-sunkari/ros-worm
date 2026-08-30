import numpy as np
import pandas as pd
import trimesh
from pathlib import Path

manifest = Path("core_resolved_flat_manifest.csv")
df = pd.read_csv(manifest)

rows = []
for _, r in df.iterrows():
    p = Path(r["stl_path"])
    m = trimesh.load_mesh(p, force="mesh")

    areas = m.area_faces if len(m.faces) else np.array([])
    edges = m.edges_unique_length if len(m.faces) else np.array([])

    rows.append({
        "name": r["safe_name"],
        "category": r["category_guess"],
        "path": str(p),
        "faces": len(m.faces),
        "verts": len(m.vertices),
        "watertight": m.is_watertight,
        "winding": m.is_winding_consistent,
        "euler": m.euler_number,
        "components": len(m.split(only_watertight=False)),
        "volume": m.volume,
        "area": m.area,
        "min_face_area": float(areas.min()) if len(areas) else None,
        "p01_face_area": float(np.percentile(areas, 1)) if len(areas) else None,
        "median_face_area": float(np.median(areas)) if len(areas) else None,
        "min_edge": float(edges.min()) if len(edges) else None,
        "p01_edge": float(np.percentile(edges, 1)) if len(edges) else None,
        "median_edge": float(np.median(edges)) if len(edges) else None,
        "bounds_min": m.bounds[0].tolist(),
        "bounds_max": m.bounds[1].tolist(),
    })

out = pd.DataFrame(rows)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 240)
print(out.to_string(index=False))

out.to_csv("resolved_stl_diagnostics.csv", index=False)
print("\nwrote resolved_stl_diagnostics.csv")
