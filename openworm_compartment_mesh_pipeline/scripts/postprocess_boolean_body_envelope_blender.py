#!/usr/bin/env python3
"""
postprocess_boolean_body_envelope_blender.py

Post-process the boolean-filled WholeBodyEnvelope:
  - optional limited mesh smoothing
  - optional shade smooth / weighted normals for visual inspection
  - optional light decimation disabled by default
  - export STL

This is meant for the boolean-cuticle-fill result where the exterior is
basically correct but looks faceted / has a rough tail transition.

Run with Blender:
  blender --background --python postprocess_boolean_body_envelope_blender.py -- [args]

Example:
  blender --background --python postprocess_boolean_body_envelope_blender.py -- \
    --input-stl /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_boolean_cuticle_fill/whole_body_envelope.stl \
    --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_boolean_cuticle_fill_smooth \
    --smooth-factor 0.25 \
    --smooth-repeat 8 \
    --shade-smooth \
    --weighted-normal
"""

from __future__ import annotations

import argparse
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
    ap.add_argument("--input-stl", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--smooth-factor", type=float, default=0.2)
    ap.add_argument("--smooth-repeat", type=int, default=5)
    ap.add_argument("--laplacian", action="store_true",
                    help="Use Laplacian Smooth modifier instead of regular Smooth.")
    ap.add_argument("--shade-smooth", action="store_true")
    ap.add_argument("--weighted-normal", action="store_true")
    ap.add_argument("--merge-distance-um", type=float, default=0.05)
    ap.add_argument("--unit-um", type=float, default=100.0)
    ap.add_argument("--keep-debug-blend", action="store_true")
    return ap.parse_args(argv)


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
    obj.data = obj.data.copy()
    obj.data.name = name + "_mesh_single_user"
    return obj


def select_active(obj):
    try:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


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


def cleanup(obj, merge_distance_units: float):
    select_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.remove_doubles(threshold=merge_distance_units)
    except Exception:
        try:
            bpy.ops.mesh.merge_by_distance(distance=merge_distance_units)
        except Exception as e:
            print("[WARN] merge failed:", repr(e))
    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception as e:
        print("[WARN] normals failed:", repr(e))
    bpy.ops.object.mode_set(mode="OBJECT")


def mesh_stats(obj):
    return {
        "vertices": int(len(obj.data.vertices)),
        "edges": int(len(obj.data.edges)),
        "polygons": int(len(obj.data.polygons)),
        "dimensions": [float(x) for x in obj.dimensions],
    }


def main():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    if not args.input_stl.exists():
        raise FileNotFoundError(args.input_stl)

    clear_scene()
    obj = import_stl(args.input_stl, "WholeBodyEnvelope_postprocess")
    select_active(obj)

    merge_units = args.merge_distance_um / args.unit_um
    cleanup(obj, merge_units)

    print("[postprocess] input:", args.input_stl)
    print("[postprocess] stats before:", mesh_stats(obj))

    if args.smooth_repeat > 0 and args.smooth_factor > 0:
        if args.laplacian:
            mod = obj.modifiers.new("light_laplacian_smooth", "LAPLACIANSMOOTH")
            mod.lambda_factor = args.smooth_factor
            mod.lambda_border = args.smooth_factor
            mod.iterations = args.smooth_repeat
            mod.use_volume_preserve = True
        else:
            mod = obj.modifiers.new("light_smooth", "SMOOTH")
            mod.factor = args.smooth_factor
            mod.iterations = args.smooth_repeat
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as e:
            raise RuntimeError(f"Could not apply smooth modifier: {e!r}")

    if args.shade_smooth:
        select_active(obj)
        for poly in obj.data.polygons:
            poly.use_smooth = True

    if args.weighted_normal:
        mod = obj.modifiers.new("weighted_normal_visual", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as e:
            print("[WARN] weighted normal apply failed:", repr(e))

    cleanup(obj, merge_units)

    out_stl = args.outdir / "whole_body_envelope.stl"
    select_active(obj)
    export_selected_stl(out_stl)

    if args.keep_debug_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.outdir / "debug_postprocess_scene.blend"))

    meta = {
        "method": "blender_postprocess_boolean_body_envelope",
        "input_stl": str(args.input_stl),
        "out_stl": str(out_stl),
        "smooth_factor": args.smooth_factor,
        "smooth_repeat": args.smooth_repeat,
        "laplacian": args.laplacian,
        "shade_smooth": args.shade_smooth,
        "weighted_normal": args.weighted_normal,
        "stats_after": mesh_stats(obj),
    }
    (args.outdir / "postprocess_meta.json").write_text(json.dumps(meta, indent=2))
    print("[postprocess] wrote:", out_stl)
    print("[postprocess] stats after:", mesh_stats(obj))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
