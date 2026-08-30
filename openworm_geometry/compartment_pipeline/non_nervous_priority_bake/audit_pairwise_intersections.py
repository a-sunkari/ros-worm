from pathlib import Path
import itertools
import trimesh
import traceback

base = Path("/home/asunkari/ros-worm/openworm_geometry")
resolved_dir = base / "compartment_pipeline/non_nervous_priority_bake/resolved_stls"

paths = {
    "ExcretorySystem": resolved_dir / "ExcretorySystem_resolved.stl",
    "ReproductiveSystem": resolved_dir / "ReproductiveSystem_resolved.stl",
    "DigestiveSystem": resolved_dir / "DigestiveSystem_resolved.stl",
    "BodyWallMuscle": resolved_dir / "BodyWallMuscle_resolved.stl",
}

meshes = {}
for name, p in paths.items():
    m = trimesh.load_mesh(p, force="mesh", process=True)
    meshes[name] = m
    print(f"[load] {name}: watertight={m.is_watertight} faces={len(m.faces)} vol={m.volume}")

print("\n=== PAIRWISE INTERSECTIONS ===")
for a, b in itertools.combinations(meshes.keys(), 2):
    ma, mb = meshes[a], meshes[b]
    print(f"\n--- {a} ∩ {b} ---")
    try:
        inter = trimesh.boolean.intersection([ma, mb], engine="manifold")
        if isinstance(inter, list):
            inter = trimesh.util.concatenate(inter)

        if inter is None or len(inter.faces) == 0:
            print("empty intersection")
            continue

        inter.process(validate=True)
        print("faces:", len(inter.faces))
        print("watertight:", inter.is_watertight)
        print("components:", len(inter.split(only_watertight=False)))
        print("volume:", inter.volume)
        print("bounds:", inter.bounds)

    except Exception:
        traceback.print_exc()
