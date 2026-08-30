from pathlib import Path
import pandas as pd
import struct
import trimesh
import numpy as np
import sys

manifest = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")
outdir.mkdir(parents=True, exist_ok=True)

category = sys.argv[1] if len(sys.argv) > 1 else "NervousSystem"

df = pd.read_csv(manifest)
rows = df[df["category_guess"] == category].copy()

out = outdir / f"{category}_raw_binary_concat.stl"

print("[raw concat] category:", category)
print("[raw concat] source count:", len(rows))
print("[raw concat] output:", out)

tri_chunks = []
total_tri = 0

global_min = np.array([np.inf, np.inf, np.inf], dtype=float)
global_max = np.array([-np.inf, -np.inf, -np.inf], dtype=float)

for _, r in rows.iterrows():
    p = Path(r["stl_path"])
    data = p.read_bytes()

    if len(data) < 84:
        raise RuntimeError(f"Too small to be binary STL: {p}")

    ntri = struct.unpack("<I", data[80:84])[0]
    expected = 84 + 50 * ntri

    if expected != len(data):
        raise RuntimeError(f"Not binary STL or size mismatch: {p} ntri={ntri} expected={expected} actual={len(data)}")

    body = data[84:]
    tri_chunks.append(body)
    total_tri += ntri

    # Bounds only; use process=False to avoid topology edits.
    m = trimesh.load_mesh(p, force="mesh", process=False)
    global_min = np.minimum(global_min, m.bounds[0])
    global_max = np.maximum(global_max, m.bounds[1])

    print("[member]", r["object_name"], "tri=", ntri, "bounds=", m.bounds.tolist())

if total_tri >= 2**32:
    raise RuntimeError("Too many triangles for binary STL uint32 count")

header = f"RAW_BINARY_CONCAT {category}".encode("ascii")[:80].ljust(80, b" ")
with open(out, "wb") as f:
    f.write(header)
    f.write(struct.pack("<I", total_tri))
    for chunk in tri_chunks:
        f.write(chunk)

print("[raw concat] wrote:", out)
print("[raw concat] triangles:", total_tri)
print("[raw concat] bounds:", np.vstack([global_min, global_max]))

# Diagnostics only. Do NOT rewrite.
m = trimesh.load_mesh(out, force="mesh", process=False)
print("[diagnostic process=False] faces:", len(m.faces))
print("[diagnostic process=False] bounds:", m.bounds)
print("[diagnostic process=False] watertight:", m.is_watertight)
print("[diagnostic process=False] components:", len(m.split(only_watertight=False)))
