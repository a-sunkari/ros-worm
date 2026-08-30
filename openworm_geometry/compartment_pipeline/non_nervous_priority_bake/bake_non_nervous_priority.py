from pathlib import Path
import trimesh
import numpy as np
import traceback

base = Path("/home/asunkari/ros-worm/openworm_geometry")
outdir = base / "compartment_pipeline/non_nervous_priority_bake/resolved_stls"
outdir.mkdir(parents=True, exist_ok=True)

inputs = {
    "WholeBodyEnvelope": base / "compartment_pipeline/body_envelope_boolean_cuticle_fill_inset05_g4clean_area1e8/whole_body_envelope.stl",
    "ExcretorySystem": base / "compartment_pipeline/baked_priority_meshes_test/ExcretorySystem_baked_union.stl",
    "ReproductiveSystem": base / "compartment_pipeline/baked_priority_meshes_test/ReproductiveSystem_baked_union.stl",
    "DigestiveSystem": base / "compartment_pipeline/baked_priority_meshes_test/DigestiveSystem_baked_union.stl",
    "BodyWallMuscle": base / "compartment_pipeline/baked_priority_meshes_test/BodyWallMuscle_baked_union.stl",
    "HypodermisSeam": base / "compartment_pipeline/baked_priority_meshes_test/HypodermisSeam_concat.stl",
}

priority = [
    "ExcretorySystem",
    "ReproductiveSystem",
    "DigestiveSystem",
    "BodyWallMuscle",
    "HypodermisSeam",
]

def clean_mesh(m, name):
    m = m.copy()
    m.remove_unreferenced_vertices()

    areas = m.area_faces
    keep = np.isfinite(areas) & (areas > 0)
    if keep.sum() != len(m.faces):
        print(f"[clean] {name}: dropping {len(m.faces) - int(keep.sum())} degenerate faces")
        m.update_faces(keep)
        m.remove_unreferenced_vertices()

    m.process(validate=True)

    if m.volume < 0:
        print(f"[clean] {name}: inverted negative-volume mesh")
        m.invert()

    return m

def load(path, name):
    print(f"\n[load] {name}: {path}")
    m = trimesh.load_mesh(path, force="mesh", process=True)
    m = clean_mesh(m, name)
    print(f"[load] {name}: watertight={m.is_watertight} comps={len(m.split(only_watertight=False))} faces={len(m.faces)} vol={m.volume}")
    print(f"[load] {name}: bounds={m.bounds}")
    if not m.is_watertight:
        raise RuntimeError(f"{name} is not watertight before bake")
    return m

meshes = {k: load(v, k) for k, v in inputs.items()}

resolved = {}
cutters = []

for name in priority:
    print(f"\n================ RESOLVING {name} ================")
    target = meshes[name]

    if cutters:
        print(f"[diff] {name}: subtracting {len(cutters)} higher-priority resolved meshes")
        try:
            r = trimesh.boolean.difference([target] + cutters, engine="manifold")
        except Exception:
            traceback.print_exc()
            raise RuntimeError(f"boolean difference failed for {name}")
    else:
        r = target.copy()

    if isinstance(r, list):
        print(f"[diff] {name}: returned list, concatenating")
        r = trimesh.util.concatenate(r)

    r = clean_mesh(r, name + "_resolved")

    out = outdir / f"{name}_resolved.stl"
    r.export(out)

    print(f"[out] {name}: {out}")
    print(f"[out] {name}: watertight={r.is_watertight} comps={len(r.split(only_watertight=False))} faces={len(r.faces)} vol={r.volume}")
    print(f"[out] {name}: bounds={r.bounds}")

    resolved[name] = r
    cutters.append(r)

print(f"\n================ RESOLVING RestOfBody ================")
body = meshes["WholeBodyEnvelope"]

try:
    rest = trimesh.boolean.difference([body] + cutters, engine="manifold")
except Exception:
    traceback.print_exc()
    raise RuntimeError("boolean difference failed for RestOfBody")

if isinstance(rest, list):
    print("[diff] RestOfBody returned list, concatenating")
    rest = trimesh.util.concatenate(rest)

rest = clean_mesh(rest, "RestOfBody_resolved")
out = outdir / "RestOfBody_resolved.stl"
rest.export(out)

print(f"[out] RestOfBody: {out}")
print(f"[out] RestOfBody: watertight={rest.is_watertight} comps={len(rest.split(only_watertight=False))} faces={len(rest.faces)} vol={rest.volume}")
print(f"[out] RestOfBody: bounds={rest.bounds}")

print("\n================ VOLUME CHECK ================")
body_vol = body.volume
sum_vol = rest.volume + sum(m.volume for m in resolved.values())
print("body volume:", body_vol)
print("resolved sum volume:", sum_vol)
print("difference:", body_vol - sum_vol)
print("relative difference:", (body_vol - sum_vol) / body_vol)
