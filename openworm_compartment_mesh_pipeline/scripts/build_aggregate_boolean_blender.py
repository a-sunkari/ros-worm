#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--")+1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources-csv", required=True, type=Path)
    ap.add_argument("--name", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--solver", choices=["EXACT", "FAST"], default="EXACT")
    ap.add_argument("--merge-distance", type=float, default=0.0005)
    ap.add_argument("--keep-debug-blend", action="store_true")
    return ap.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_stl(path: Path, name: str):
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_mesh"
    obj.data = obj.data.copy()
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


def cleanup(obj, merge_distance):
    select_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.mesh.remove_doubles(threshold=merge_distance)
    except Exception:
        bpy.ops.mesh.merge_by_distance(distance=merge_distance)
    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception:
        pass
    bpy.ops.object.mode_set(mode="OBJECT")


def export_selected(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(bpy.ops.wm, "stl_export"):
        try:
            bpy.ops.wm.stl_export(filepath=str(path), export_selected_objects=True, ascii_format=False, apply_modifiers=True)
            return
        except Exception:
            pass
    bpy.ops.export_mesh.stl(filepath=str(path), use_selection=True, ascii=False, use_mesh_modifiers=True)


def boolean_union(base, tool, solver):
    select_active(base)
    mod = base.modifiers.new("union_" + tool.name, "BOOLEAN")
    mod.operation = "UNION"
    mod.object = tool
    mod.solver = solver
    bpy.ops.object.modifier_apply(modifier=mod.name)


def main():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.sources_csv.open()))
    if not rows:
        raise SystemExit("No source rows")

    clear_scene()

    objs = []
    for i, r in enumerate(rows):
        p = Path(r["stl_path"])
        if not p.exists():
            print("[WARN] missing:", p)
            continue
        safe = r.get("safe_name") or r.get("object_name") or f"obj{i}"
        obj = import_stl(p, safe)
        cleanup(obj, args.merge_distance)
        objs.append(obj)
        print(f"[aggregate] imported {i+1}/{len(rows)} {safe}")

    if not objs:
        raise SystemExit("No objects imported")

    base = objs[0]
    base.name = args.name + "_aggregate_working"

    failures = []
    for i, obj in enumerate(objs[1:], start=2):
        try:
            print(f"[aggregate] boolean {i}/{len(objs)}: {obj.name}")
            boolean_union(base, obj, args.solver)
            bpy.data.objects.remove(obj, do_unlink=True)
            cleanup(base, args.merge_distance)
        except Exception as e:
            print("[WARN] boolean failed:", obj.name, repr(e))
            failures.append({"object": obj.name, "error": repr(e)})

    base.name = args.name
    base.data.name = args.name + "_mesh"
    cleanup(base, args.merge_distance)

    select_active(base)
    out_stl = args.outdir / f"{args.name}.stl"
    export_selected(out_stl)

    if args.keep_debug_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.outdir / f"{args.name}_debug.blend"))

    meta = {
        "name": args.name,
        "sources_csv": str(args.sources_csv),
        "source_count": len(rows),
        "imported_count": len(objs),
        "boolean_failures": failures,
        "out_stl": str(out_stl),
        "vertices": len(base.data.vertices),
        "faces": len(base.data.polygons),
    }
    (args.outdir / f"{args.name}_meta.json").write_text(json.dumps(meta, indent=2))
    print("[aggregate] wrote:", out_stl)
    print("[aggregate] failures:", len(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
