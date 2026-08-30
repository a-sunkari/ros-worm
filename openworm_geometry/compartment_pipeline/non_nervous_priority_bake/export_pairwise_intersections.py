from pathlib import Path
import itertools
import trimesh

base = Path("/home/asunkari/ros-worm/openworm_geometry")
resolved_dir = base / "compartment_pipeline/non_nervous_priority_bake/resolved_stls"
outdir = base / "compartment_pipeline/non_nervous_priority_bake/pairwise_intersections"
outdir.mkdir(parents=True, exist_ok=True)

paths = {
    "ExcretorySystem": resolved_dir / "ExcretorySystem_resolved.stl",
    "ReproductiveSystem": resolved_dir / "ReproductiveSystem_resolved.stl",
    "DigestiveSystem": resolved_dir / "DigestiveSystem_resolved.stl",
    "BodyWallMuscle": resolved_dir / "BodyWallMuscle_resolved.stl",
}

meshes = {k: trimesh.load_mesh(p, force="mesh", process=True) for k, p in paths.items()}

for a, b in itertools.combinations(meshes.keys(), 2):
    print(f"\n--- {a} ∩ {b} ---")
    inter = trimesh.boolean.intersection([meshes[a], meshes[b]], engine="manifold")
    if isinstance(inter, list):
        inter = trimesh.util.concatenate(inter)

    if inter is None or len(inter.faces) == 0:
        print("empty")
        continue

    inter.export(outdir / f"{a}_INTERSECT_{b}.stl")
    print("wrote:", outdir / f"{a}_INTERSECT_{b}.stl")
    print("faces:", len(inter.faces))
    print("volume:", inter.volume)
    print("bounds:", inter.bounds)

print("\nDone:", outdir)
