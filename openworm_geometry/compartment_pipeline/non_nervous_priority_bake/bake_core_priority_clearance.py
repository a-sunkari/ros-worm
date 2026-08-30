from pathlib import Path
import trimesh
import numpy as np
import traceback

base = Path("/home/asunkari/ros-worm/openworm_geometry")
outdir = base / "compartment_pipeline/non_nervous_priority_bake/resolved_stls_clearance_5um"
outdir.mkdir(parents=True, exist_ok=True)

CLEARANCE_UM = 5.0
CLEARANCE_MODEL = CLEARANCE_UM / 100.0  # 1 model unit = 100 um

inputs = {
    "ExcretorySystem": base / "compartment_pipeline/baked_priority_meshes_test/ExcretorySystem_baked_union.stl",
    "ReproductiveSystem": base / "compartment_pipeline/baked_priority_meshes_test/ReproductiveSystem_baked_union.stl",
    "DigestiveSystem": base / "compartment_pipeline/baked_priority_meshes_test/DigestiveSystem_baked_union.stl",
    "BodyWallMuscle": base / "compartment_pipeline/baked_priority_meshes_test/BodyWallMuscle_baked_union.stl",
}

priority = [
    "ExcretorySystem",
    "ReproductiveSystem",
    "DigestiveSystem",
    "BodyWallMuscle",
]

def clean(m, name):
    m = m.copy()
    m.remove_unreferenced_vertices()
    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0)
    if keep.sum() != len(m.faces):
        print(f"[clean] {name}: drop {len(m.faces) - int(keep.sum())} degenerate faces")
        m.update_faces(keep)
        m.remove_unreferenced_vertices()
    try:
        trimesh.repair.fix_normals(m)
    except Exception:
        pass
    m.process(validate=True)
    if m.volume < 0:
        m.invert()
    return m

def inflate_by_normals(m, delta, name):
    x = clean(m, name + "_preinflate")
    normals = x.vertex_normals
    verts = x.vertices + normals * delta
    y = trimesh.Trimesh(vertices=verts, faces=x.faces.copy(), process=True)
    y = clean(y, name + f"_inflated_{CLEARANCE_UM}um")
    print(f"[inflate] {name}: delta_model={delta} watertight={y.is_watertight} faces={len(y.faces)} vol={y.volume}")
    return y

def load(name):
    p = inputs[name]
    m = trimesh.load_mesh(p, force="mesh", process=True)
    m = clean(m, name)
    print(f"[load] {name}: watertight={m.is_watertight} comps={len(m.split(only_watertight=False))} faces={len(m.faces)} vol={m.volume}")
    return m

raw = {name: load(name) for name in priority}

resolved = {}
inflated_cutters = {}

for name in priority:
    print(f"\n================ RESOLVE {name} ================")
    r = raw[name].copy()

    for cutter_name in resolved.keys():
        cutter = inflated_cutters[cutter_name]
        print(f"[diff] {name} -= inflated {cutter_name} ({CLEARANCE_UM} um clearance)")
        try:
            r2 = trimesh.boolean.difference([r, cutter], engine="manifold")
        except Exception:
            traceback.print_exc()
            raise RuntimeError(f"failed subtract inflated {cutter_name} from {name}")

        if isinstance(r2, list):
            r2 = trimesh.util.concatenate(r2)

        r = clean(r2, f"{name}_minus_{cutter_name}")
        print(f"[post] {name}: watertight={r.is_watertight} comps={len(r.split(only_watertight=False))} faces={len(r.faces)} vol={r.volume}")

    out = outdir / f"{name}_resolved.stl"
    r.export(out)
    print(f"[out] {out}")
    print(f"[out] {name}: watertight={r.is_watertight} comps={len(r.split(only_watertight=False))} faces={len(r.faces)} vol={r.volume} bounds={r.bounds}")

    resolved[name] = r
    inflated_cutters[name] = inflate_by_normals(r, CLEARANCE_MODEL, name)

print("\nDONE")
