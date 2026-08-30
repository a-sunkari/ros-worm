#!/usr/bin/env python3
"""
make_filled_body_from_cuticle_boolean_blender.py

Blender-headless CAD-style workflow:

    original OpenWorm Cuticle hollow shell
    + an inward-offset filler solid
    -> Boolean UNION
    -> filled WholeBodyEnvelope whose outer surface should be dominated by the true Cuticle exterior.

This avoids manually drawing a Bezier centerline and avoids using a voxel phantom as
the final geometry.

Run with Blender, not python:
    blender --background --python make_filled_body_from_cuticle_boolean_blender.py -- [args]

Example:
    blender --background --python make_filled_body_from_cuticle_boolean_blender.py -- \
      --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv \
      --filler-stl /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_surface_offset_tuned1_capped/whole_body_envelope.stl \
      --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_boolean_cuticle_fill \
      --cuticle-name Cuticle \
      --inset-um 2.0 \
      --unit-um 100.0

Notes:
- inset-um pushes the filler inward before union, so the boolean's outer surface remains
  the real Cuticle exterior instead of the filler.
- If the filler is too far inward and doesn't overlap the cuticle shell, union may leave
  disconnected internal pieces. Reduce inset-um.
- If the filler protrudes outside and affects the exterior, increase inset-um.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


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
    return ap.parse_args(argv)


def read_manifest_path(manifest: Path, object_name: str) -> Path:
    with manifest.open(newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        name_col = next((c for c in ["object_name", "name", "object", "Object"] if c in cols), None)
        path_col = next((c for c in ["stl_path", "path", "filepath", "file_path", "stl"] if c in cols), None)
        if name_col is None or path_col is None:
            raise RuntimeError(f"Could not infer columns from manifest: {cols}")
        for row in reader:
            if row[name_col] == object_name:
                return Path(row[path_col])
    raise FileNotFoundError(f"{object_name!r} not found in {manifest}")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_stl(path: Path, name: str):
    # Blender 4 has wm.stl_import; older Blender has import_mesh.stl
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    elif hasattr(bpy.ops.import_mesh, "stl"):
        bpy.ops.import_mesh.stl(filepath=str(path))
    else:
        raise RuntimeError("No STL import operator found")
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_mesh"
    return obj


def export_selected_stl(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(bpy.ops.wm, "stl_export"):
        try:
            bpy.ops.wm.stl_export(filepath=str(path), export_selected_objects=True, ascii_format=False, apply_modifiers=True)
            return
        except Exception as e:
            print("[WARN] wm.stl_export failed, trying export_mesh.stl:", repr(e))
    if hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=str(path), use_selection=True, ascii=False, use_mesh_modifiers=True)
        return
    raise RuntimeError("No STL export operator found")


def set_origin_and_apply_transforms(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def displace_inward(obj, inset_units: float):
    # Displace along vertex normals inward.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Make sure normals are coherent before inward displacement.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    mod = obj.modifiers.new("inset_filler_along_normals", "DISPLACE")
    mod.strength = -float(inset_units)
    mod.direction = "NORMAL"
    bpy.ops.object.modifier_apply(modifier=mod.name)


def cleanup_mesh(obj, merge_distance_units: float):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.remove_doubles(threshold=merge_distance_units)
    except Exception:
        bpy.ops.mesh.merge_by_distance(distance=merge_distance_units)

    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def boolean_union(base, tool, solver="EXACT"):
    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True)
    bpy.context.view_layer.objects.active = base

    mod = base.modifiers.new("union_cuticle_plus_inner_filler", "BOOLEAN")
    mod.operation = "UNION"
    mod.object = tool
    mod.solver = solver
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        raise RuntimeError(f"Boolean union failed with solver={solver}: {e!r}")


def mesh_stats(obj):
    mesh = obj.data
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "bounds": [[float(x) for x in obj.bound_box[i]] for i in range(8)],
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

    set_origin_and_apply_transforms(cuticle)
    set_origin_and_apply_transforms(filler)

    inset_units = args.inset_um / args.unit_um
    merge_units = args.merge_distance_um / args.unit_um

    print("[boolean fill] cuticle:", cuticle_stl)
    print("[boolean fill] filler:", args.filler_stl)
    print("[boolean fill] inset_um:", args.inset_um, "inset_units:", inset_units)

    # Save pre-inset debug copy
    bpy.ops.object.select_all(action="DESELECT")
    filler.select_set(True)
    bpy.context.view_layer.objects.active = filler
    export_selected_stl(args.outdir / "debug_filler_before_inset.stl")

    displace_inward(filler, inset_units)
    cleanup_mesh(filler, merge_units)

    bpy.ops.object.select_all(action="DESELECT")
    filler.select_set(True)
    bpy.context.view_layer.objects.active = filler
    export_selected_stl(args.outdir / "debug_filler_after_inset.stl")

    cleanup_mesh(cuticle, merge_units)
    boolean_union(cuticle, filler, solver=args.boolean_solver)
    cleanup_mesh(cuticle, merge_units)

    # Delete filler object after union, so exported object is only final body.
    bpy.data.objects.remove(filler, do_unlink=True)

    cuticle.name = "WholeBodyEnvelope_boolean_cuticle_fill"
    cuticle.data.name = "WholeBodyEnvelope_boolean_cuticle_fill_mesh"

    bpy.ops.object.select_all(action="DESELECT")
    cuticle.select_set(True)
    bpy.context.view_layer.objects.active = cuticle

    out_stl = args.outdir / "whole_body_envelope.stl"
    export_selected_stl(out_stl)

    if args.keep_debug_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.outdir / "debug_boolean_fill_scene.blend"))

    meta = {
        "method": "cuticle_shell_boolean_union_with_inset_filler",
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
    print("[boolean fill] wrote:", out_stl)
    print("[boolean fill] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
