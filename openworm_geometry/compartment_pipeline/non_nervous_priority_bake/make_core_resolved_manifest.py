from pathlib import Path
import pandas as pd
import trimesh

base = Path("/home/asunkari/ros-worm/openworm_geometry")
template = pd.read_csv(base / "object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv")

stldir = base / "compartment_pipeline/non_nervous_priority_bake/resolved_stls"
body = base / "compartment_pipeline/body_envelope_boolean_cuticle_fill_inset05_g4clean_area1e8/whole_body_envelope.stl"

items = [
    ("WholeBodyEnvelope", "WholeBodyEnvelope", "whole_body_parent", body),
    ("ExcretorySystem", "ExcretorySystem", "ExcretorySystem", stldir / "ExcretorySystem_resolved.stl"),
    ("ReproductiveSystem", "ReproductiveSystem", "ReproductiveSystem", stldir / "ReproductiveSystem_resolved.stl"),
    ("DigestiveSystem", "DigestiveSystem", "DigestiveSystem", stldir / "DigestiveSystem_resolved.stl"),
    ("BodyWallMuscle", "BodyWallMuscle", "BodyWallMuscle", stldir / "BodyWallMuscle_resolved.stl"),
]

rows = []

for object_name, safe_name, category, stl in items:
    if not stl.exists():
        raise FileNotFoundError(stl)

    m = trimesh.load_mesh(stl, force="mesh", process=True)

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
        "repair_watertight_after": bool(m.is_watertight),
        "repair_winding_after": True,
        "repair_faces_after": len(m.faces),
    }

    for k, v in vals.items():
        if k in row:
            row[k] = v

    rows.append(row)
    print(object_name, "watertight=", m.is_watertight, "faces=", len(m.faces), "volume=", m.volume)

out = base / "compartment_pipeline/non_nervous_priority_bake/core_resolved_flat_manifest.csv"
pd.DataFrame(rows, columns=template.columns).to_csv(out, index=False)
print("wrote:", out)
