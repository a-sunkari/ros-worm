import trimesh
from pathlib import Path

obj = Path("OBJ/Adult.obj")
outdir = Path("split_adult_stls")
outdir.mkdir(exist_ok=True)

scene = trimesh.load(obj, force="scene")

print("geometries:", list(scene.geometry.keys()))

for name, geom in scene.geometry.items():
    safe = name.replace(" ", "_").replace("/", "_")
    out = outdir / f"{safe}.stl"
    geom.export(out)

    print(
        safe,
        "faces", len(geom.faces),
        "verts", len(geom.vertices),
        "watertight", geom.is_watertight,
        "winding", geom.is_winding_consistent,
        "euler", geom.euler_number,
        "components", len(geom.split(only_watertight=False)),
        "volume", geom.volume,
        "bounds", geom.bounds,
        "wrote", out,
    )
