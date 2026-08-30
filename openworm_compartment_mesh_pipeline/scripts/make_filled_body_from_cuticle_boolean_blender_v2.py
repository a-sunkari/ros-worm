#!/usr/bin/env python3
"""
make_filled_body_from_cuticle_boolean_blender_v2.py

CAD-style fill workflow in Blender:

    Cuticle hollow shell + inward-offset filler solid -> Boolean UNION

The intended result is a filled WholeBodyEnvelope whose outer surface comes
from the true Cuticle mesh as much as possible, while the filler closes the
hollow interior.

Run with Blender:
    blender --background --python make_filled_body_from_cuticle_boolean_blender_v2.py -- [args]

Example:
    blender --background --python make_filled_body_from_cuticle_boolean_blender_v2.py -- \
      --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv \
      --filler-stl /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_surface_offset_tuned1_capped/whole_body_envelope.stl \
      --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_boolean_cuticle_fill \
      --cuticle-name Cuticle \
      --inset-um 2.0 \
      --unit-um 100.0 \
      --boolean-solver EXACT \
      --keep-debug-blend
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--filler-stl", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--cuticle-name", default="Cuticle")
    ap.add_argument("--inset-um", type=float, default=2.0)
    ap.add_argument("--unit-um", type=float, default=100.0)
    ap.add_argument("--boolean-solver", choices=["EXACT", "FAST"], default="EXACT")
    ap.add_argument("--merge-distance-um", type=float, default=0.05)
    ap.add_argument("--keep-debug-blend", action="store_true")
    ap.add_argument("--export-debug-stls", action="store_true", default=True)
    return ap.parse_args(argv)


def read_manifest_path(manifest: Path, object_name: str) -> Path:
    with manifest.open(newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        name_col = next((c for c in ["object_name", "name", "object", "Object"] if c in cols), None)
        path_col = next((c for c in ["stl_path", "path", "filepath", "file_path", "stl"] if c in cols), None)
        if name_col is None or path_col is None:
            raise RuntimeError(f"Could not infer manifest columns from: {cols}")
        for row in reader:
            if row[name_col] == object_name:
                return Path(row[path_col])
    raise FileNotFoundError(f"{object_name!r} not found in {manifest}")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_stl(path: Path, name: str):
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    elif hasattr(bpy.ops.import_mesh, "stl"):
        bpy.ops.import_mesh.stl(filepath=str(path))
    else:
        raise RuntimeError("No STL import operator found")

    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_mesh"

    # Critical for Blender 4.x:
    # Imported STL data can behave as multi-user in some contexts. Modifiers/apply
    # can fail unless the mesh datablock is explicitly copied and linked only here.
    obj.data = obj.data.copy()
    obj.data.name = name + "_mesh_single_user"
    return obj


def select_active(obj):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def export_selected_stl(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(bpy.ops.wm, "stl_export"):
        try:
            bpy.ops.wm.stl_export(
                filepath=str(path),
                export_selected_objects=True,
                ascii_format=False,
                apply_modifiers=True,
            )
            return
        except Exception as e:
            print("[WARN] wm.stl_export failed, trying export_mesh.stl:", repr(e))
    if hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(
            filepath=str(path),
            use_selection=True,
            ascii=False,
            use_mesh_modifiers=True,
        )
        return
    raise RuntimeError("No STL export operator found")


def apply_scale_only(obj):
    # Avoid applying location/rotation. Only scale if non-identity.
    select_active(obj)
    try:
        if any(abs(v - 1.0) > 1e-12 for v in obj.scale):
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception as e:
        print(f"[WARN] transform_apply scale skipped for {obj.name}: {e!r}")


def cleanup_mesh(obj, merge_distance_units: float):
    select_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    try:
        bpy.ops.mesh.remove_doubles(threshold=merge_distance_units)
    except Exception:
        try:
            bpy.ops.mesh.merge_by_distance(distance=merge_distance_units)
        except Exception as e:
            print(f"[WARN] merge by distance failed for {obj.name}: {e!r}")

    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception as e:
        print(f"[WARN] normals_make_consistent failed for {obj.name}: {e!r}")

    bpy.ops.object.mode_set(mode="OBJECT")


def displace_inward(obj, inset_units: float):
    select_active(obj)

    # Ensure normals are coherent before normal-direction displacement.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception as e:
        print(f"[WARN] normal consistency before displace failed: {e!r}")
    bpy.ops.object.mode_set(mode="OBJECT")

    mod = obj.modifiers.new("inset_filler_along_normals", "DISPLACE")
    mod.strength = -float(inset_units)
    mod.direction = "NORMAL"
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        raise RuntimeError(f"Could not apply inward displacement modifier: {e!r}")


def boolean_union(base, tool, solver="EXACT"):
    select_active(base)
    mod = base.modifiers.new("union_cuticle_plus_inner_filler", "BOOLEAN")
    mod.operation = "UNION"
    mod.object = tool
    mod.solver = solver
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        raise RuntimeError(f"Boolean union failed with solver={solver}: {e!r}")


def mesh_stats(obj):
    # bound_box is local. For this workflow transforms should be identity-ish after import.
    return {
        "vertices": int(len(obj.data.vertices)),
        "edges": int(len(obj.data.edges)),
        "polygons": int(len(obj.data.polygons)),
        "dimensions": [float(x) for x in obj.dimensions],
        "location": [float(x) for x in obj.location],
        "scale": [float(x) for x in obj.scale],
    }


def main():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    cuticle_stl = read_manifest_path(args.manifest, args.cuticle_name)
    if not cuticle_stl.exists():
        raise FileNotFoundError(cuticle_stl)
    if not args.filler_stl.exists():
        raise FileNotFoundError(args.filler_stl)

    clear_scene()

    cuticle = import_stl(cuticle_stl, "Cuticle_source_shell")
    filler = import_stl(args.filler_stl, "Inner_filler_source")

    apply_scale_only(cuticle)
    apply_scale_only(filler)

    inset_units = args.inset_um / args.unit_um
    merge_units = args.merge_distance_um / args.unit_um

    print("[boolean fill v2] cuticle:", cuticle_stl)
    print("[boolean fill v2] filler:", args.filler_stl)
    print("[boolean fill v2] inset_um:", args.inset_um, "inset_units:", inset_units)
    print("[boolean fill v2] merge_distance_um:", args.merge_distance_um, "merge_units:", merge_units)
    print("[boolean fill v2] cuticle stats before:", mesh_stats(cuticle))
    print("[boolean fill v2] filler stats before:", mesh_stats(filler))

    if args.export_debug_stls:
        select_active(filler)
        export_selected_stl(args.outdir / "debug_filler_before_inset.stl")
        select_active(cuticle)
        export_selected_stl(args.outdir / "debug_cuticle_before_union.stl")

    displace_inward(filler, inset_units)
    cleanup_mesh(filler, merge_units)

    if args.export_debug_stls:
        select_active(filler)
        export_selected_stl(args.outdir / "debug_filler_after_inset.stl")

    cleanup_mesh(cuticle, merge_units)
    boolean_union(cuticle, filler, solver=args.boolean_solver)
    cleanup_mesh(cuticle, merge_units)

    # Delete filler after union.
    bpy.data.objects.remove(filler, do_unlink=True)

    cuticle.name = "WholeBodyEnvelope_boolean_cuticle_fill"
    cuticle.data.name = "WholeBodyEnvelope_boolean_cuticle_fill_mesh"

    select_active(cuticle)
    out_stl = args.outdir / "whole_body_envelope.stl"
    export_selected_stl(out_stl)

    # Write simple manifest for downstream validators.
    with (args.outdir / "whole_body_parent_manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["object_name", "stl_path"])
        w.writeheader()
        w.writerow({"object_name": "WholeBodyEnvelope", "stl_path": str(out_stl)})

    if args.keep_debug_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.outdir / "debug_boolean_fill_scene.blend"))

    meta = {
        "method": "cuticle_shell_boolean_union_with_inset_filler_v2",
        "cuticle_stl": str(cuticle_stl),
        "filler_stl": str(args.filler_stl),
        "out_stl": str(out_stl),
        "inset_um": args.inset_um,
        "unit_um": args.unit_um,
        "merge_distance_um": args.merge_distance_um,
        "boolean_solver": args.boolean_solver,
        "final_mesh_stats_blender": mesh_stats(cuticle),
    }
    (args.outdir / "boolean_fill_meta.json").write_text(json.dumps(meta, indent=2))
    print("[boolean fill v2] wrote:", out_stl)
    print("[boolean fill v2] final stats:", mesh_stats(cuticle))
    print("[boolean fill v2] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
