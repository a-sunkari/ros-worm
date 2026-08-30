from pathlib import Path
import pandas as pd
import trimesh

base = Path("/home/asunkari/ros-worm/openworm_geometry")
baked = base / "compartment_pipeline/baked_priority_meshes_test"
template = pd.read_csv(base / "object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv")

items = [
    (
        "WholeBodyEnvelope",
        "WholeBodyEnvelope",
        "whole_body_parent",
        base / "compartment_pipeline/body_envelope_boolean_cuticle_fill_inset05_g4clean_area1e8/whole_body_envelope.stl",
    ),
    (
        "NervousSystem",
        "NervousSystem",
        "NervousSystem",
        baked / "NervousSystem_concat_no_global_process.stl",
    ),
    (
        "ExcretorySystem",
        "ExcretorySystem",
        "ExcretorySystem",
        baked / "ExcretorySystem_baked_union.stl",
    ),
    (
        "ReproductiveSystem",
        "ReproductiveSystem",
        "ReproductiveSystem",
        baked / "ReproductiveSystem_baked_union.stl",
    ),
    (
        "DigestiveSystem",
        "DigestiveSystem",
        "DigestiveSystem",
        baked / "DigestiveSystem_baked_union.stl",
    ),
    (
        "BodyWallMuscle",
        "BodyWallMuscle",
        "BodyWallMuscle",
        baked / "BodyWallMuscle_baked_union.stl",
    ),
    (
        "HypodermisSeam",
        "HypodermisSeam",
        "HypodermisSeam",
        baked / "HypodermisSeam_concat.stl",
    ),
]

rows = []

for object_name, safe_name, category, stl in items:
    if not stl.exists():
        raise FileNotFoundError(stl)

    m = trimesh.load_mesh(stl, force="mesh", process=True)
    if m.volume < 0:
        m.invert()

    row = {c: "" for c in template.columns}
    row["object_name"] = object_name
    row["safe_name"] = safe_name
    row["category_guess"] = category
    row["stl_path"] = str(stl)

    vals = {
        "raw_triangles": len(m.faces),
        "exported_triangles": len(m.faces),
        "skipped_degenerate": 0,
        "min_x": m.bounds[0, 0],
        "min_y": m.bounds[0, 1],
        "min_z": m.bounds[0, 2],
        "max_x": m.bounds[1, 0],
        "max_y": m.bounds[1, 1],
        "max_z": m.bounds[1, 2],
        "span_x": m.extents[0],
        "span_y": m.extents[1],
        "span_z": m.extents[2],
        "repair_used_meshfix": False,
        "repair_watertight_after": m.is_watertight,
        "repair_winding_after": True,
        "repair_faces_after": len(m.faces),
    }

    for k, v in vals.items():
        if k in row:
            row[k] = v

    rows.append(row)

    print(object_name)
    print("  file:", stl)
    print("  watertight:", m.is_watertight)
    print("  components:", len(m.split(only_watertight=False)))
    print("  faces:", len(m.faces))
    print("  volume:", m.volume)
    print("  bounds:", m.bounds)

out = baked / "baked_full_flat_manifest.csv"
pd.DataFrame(rows, columns=template.columns).to_csv(out, index=False)
print("\nwrote:", out)
