from pathlib import Path
import trimesh
import numpy as np
import sys

try:
    import pymeshfix
    HAS_MESHFIX = True
except Exception:
    HAS_MESHFIX = False

indir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test")

targets = [
    indir / "HypodermisSeam_baked_union.stl",
    indir / "NervousSystem_baked_union.stl",
]

def clean_basic(m):
    m = m.copy()
    m.remove_unreferenced_vertices()
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

def meshfix_repair(m):
    if not HAS_MESHFIX:
        print("[repair] pymeshfix not installed; using basic trimesh repair only")
        return m

    print("[repair] using pymeshfix")
    v = np.asarray(m.vertices, dtype=np.float64)
    f = np.asarray(m.faces, dtype=np.int32)

    mf = pymeshfix.MeshFix(v, f)

    # pymeshfix versions differ in accepted keyword args.
    # The current documented output arrays are mf.points and mf.faces.
    try:
        mf.repair(joincomp=True, remove_smallest_components=False)
    except TypeError:
        try:
            mf.repair(joincomp=True)
        except TypeError:
            mf.repair()

    repaired = trimesh.Trimesh(vertices=mf.points, faces=mf.faces, process=True)
    repaired = clean_basic(repaired)
    return repaired

for p in targets:
    print("\n=== repairing", p.name, "===")
    m = trimesh.load_mesh(p, force="mesh", process=True)
    m = clean_basic(m)

    print("[before] watertight:", m.is_watertight)
    print("[before] components:", len(m.split(only_watertight=False)))
    print("[before] faces:", len(m.faces))
    print("[before] volume:", m.volume)
    print("[before] bounds:", m.bounds)

    r = meshfix_repair(m)
    r = clean_basic(r)

    out = p.with_name(p.stem + "_repaired.stl")
    r.export(out)

    print("[after] wrote:", out)
    print("[after] watertight:", r.is_watertight)
    print("[after] components:", len(r.split(only_watertight=False)))
    print("[after] faces:", len(r.faces))
    print("[after] volume:", r.volume)
    print("[after] bounds:", r.bounds)
