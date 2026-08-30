#!/usr/bin/env python3
"""
Batch-clean per-object OpenWorm STL files in Blender.

Designed for the object-preserving export pipeline:
  one Blender object -> one STL -> one Geant4 physical volume.

This script is intentionally conservative by default. It fixes the easy/low-risk
mesh issues first: duplicate vertices, loose geometry, degenerate faces, and
inconsistent normals. Hole filling is disabled by default because it can alter
thin biological structures; enable it only as a second pass.

Run with Blender, e.g.:
  blender --background --python clean_openworm_object_stls_blender.py -- \
    --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls/openworm_object_stl_manifest.csv \
    --outdir /home/asunkari/ros-worm/openworm_geometry/object_stls_clean_conservative \
    --merge-distance 1e-6 \
    --degenerate-threshold 1e-7 \
    --fill-holes-max-sides 0

Units note:
  Your STLs are in the original Blender/model coordinates. Earlier scale markers
  imply ~0.01 model units = 1 um, so:
    1e-6 model units ~= 0.1 nm
    1e-5 model units ~= 1 nm
    1e-4 model units ~= 10 nm
Keep merge distances tiny. Do not use large merge distances unless you are
intentionally simplifying anatomy.
"""

import bpy
import csv
import json
import math
import os
import sys
import time
from mathutils import Vector


def argv_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def parse_args(argv):
    opts = {
        "manifest": None,
        "outdir": None,
        "merge_distance": 1e-6,
        "degenerate_threshold": 1e-7,
        "fill_holes_max_sides": 0,
        "limit": 0,
        "start_index": 0,
        "flip_negative_volume": True,
    }
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--manifest":
            opts["manifest"] = argv[i + 1]; i += 2
        elif a == "--outdir":
            opts["outdir"] = argv[i + 1]; i += 2
        elif a == "--merge-distance":
            opts["merge_distance"] = float(argv[i + 1]); i += 2
        elif a == "--degenerate-threshold":
            opts["degenerate_threshold"] = float(argv[i + 1]); i += 2
        elif a == "--fill-holes-max-sides":
            opts["fill_holes_max_sides"] = int(argv[i + 1]); i += 2
        elif a == "--limit":
            opts["limit"] = int(argv[i + 1]); i += 2
        elif a == "--start-index":
            opts["start_index"] = int(argv[i + 1]); i += 2
        elif a == "--no-flip-negative-volume":
            opts["flip_negative_volume"] = False; i += 1
        else:
            raise SystemExit(f"Unknown argument: {a}")
    if not opts["manifest"]:
        raise SystemExit("Missing --manifest")
    if not opts["outdir"]:
        raise SystemExit("Missing --outdir")
    return opts


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def import_stl(path):
    clear_scene()
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not objs:
        raise RuntimeError(f"No mesh object imported from {path}")
    # If importer creates multiple objects, join them while preserving world placement.
    if len(objs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
    obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    return obj


def export_selected_stl(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, ascii_format=False)
    else:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True, ascii=False)


def tri_area(a, b, c):
    return 0.5 * ((b - a).cross(c - a)).length


def signed_volume_mesh(mesh, matrix_world=None):
    if matrix_world is None:
        matrix_world = None
    mesh.calc_loop_triangles()
    verts = mesh.vertices
    vol = 0.0
    for tri in mesh.loop_triangles:
        p0 = verts[tri.vertices[0]].co
        p1 = verts[tri.vertices[1]].co
        p2 = verts[tri.vertices[2]].co
        if matrix_world is not None:
            p0 = matrix_world @ p0
            p1 = matrix_world @ p1
            p2 = matrix_world @ p2
        vol += p0.dot(p1.cross(p2)) / 6.0
    return vol


def mesh_stats(obj, area_eps=1e-18):
    me = obj.data
    me.update()
    me.calc_loop_triangles()
    # Build edge -> face count map from polygon loops, independent of mesh.edges metadata.
    edge_face_counts = {}
    degenerate_faces = 0
    for poly in me.polygons:
        vs = list(poly.vertices)
        if len(vs) < 3:
            degenerate_faces += 1
        # triangulated area check
        if poly.area <= area_eps:
            degenerate_faces += 1
        for i in range(len(vs)):
            a = vs[i]; b = vs[(i + 1) % len(vs)]
            if a == b:
                continue
            e = tuple(sorted((a, b)))
            edge_face_counts[e] = edge_face_counts.get(e, 0) + 1
    boundary_edges = sum(1 for c in edge_face_counts.values() if c == 1)
    nonmanifold_edges = sum(1 for c in edge_face_counts.values() if c != 2)
    loose_verts = 0
    used = set()
    for e in edge_face_counts:
        used.update(e)
    loose_verts = len(me.vertices) - len(used)
    vol = signed_volume_mesh(me, obj.matrix_world)
    return {
        "vertices": len(me.vertices),
        "edges_counted": len(edge_face_counts),
        "faces": len(me.polygons),
        "triangles": len(me.loop_triangles),
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "degenerate_faces": degenerate_faces,
        "loose_vertices": loose_verts,
        "signed_volume": vol,
        "volume_abs": abs(vol),
        "watertight_edge_test": int(boundary_edges == 0 and nonmanifold_edges == 0),
    }


def call_op_safely(label, fn, **kwargs):
    try:
        return fn(**kwargs)
    except Exception as e:
        print(f"[WARN] {label} failed: {e}")
        return None


def cleanup_object(obj, opts):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Apply mesh cleanup in edit mode. This preserves object/world coordinates.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Merge duplicate/nearly duplicate vertices. Use very small dist.
    try:
        bpy.ops.mesh.remove_doubles(threshold=opts["merge_distance"])
    except Exception:
        try:
            bpy.ops.mesh.merge_by_distance(distance=opts["merge_distance"])
        except Exception as e:
            print(f"[WARN] merge/remove doubles failed: {e}")

    # Remove degenerate edges/faces below threshold.
    call_op_safely("dissolve_degenerate", bpy.ops.mesh.dissolve_degenerate, threshold=opts["degenerate_threshold"])

    # Delete loose vertices/edges.
    call_op_safely("delete_loose", bpy.ops.mesh.delete_loose)

    # Optional small-hole fill. Keep disabled first pass unless explicitly requested.
    if opts["fill_holes_max_sides"] and opts["fill_holes_max_sides"] > 0:
        bpy.ops.mesh.select_all(action='SELECT')
        call_op_safely("fill_holes", bpy.ops.mesh.fill_holes, sides=opts["fill_holes_max_sides"])

    # Make normals consistent. This is local consistency, not a guarantee of correct global inside/outside.
    bpy.ops.mesh.select_all(action='SELECT')
    call_op_safely("normals_make_consistent", bpy.ops.mesh.normals_make_consistent, inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.data.update()

    # If the mesh is closed-ish and signed volume is negative, flip all normals.
    st = mesh_stats(obj)
    if opts["flip_negative_volume"] and st["signed_volume"] < 0:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        call_op_safely("flip_normals_negative_volume", bpy.ops.mesh.flip_normals)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.update()

    return obj


def main():
    opts = parse_args(argv_after_dash())
    manifest = os.path.abspath(opts["manifest"])
    outdir = os.path.abspath(opts["outdir"])
    stldir = os.path.join(outdir, "stl")
    os.makedirs(stldir, exist_ok=True)

    with open(manifest, newline='') as f:
        rows = list(csv.DictReader(f))

    if opts["start_index"]:
        rows = rows[opts["start_index"]:]
    if opts["limit"] and opts["limit"] > 0:
        rows = rows[:opts["limit"]]

    cleaned_rows = []
    t0 = time.time()
    print(f"[OpenWorm clean] input manifest: {manifest}")
    print(f"[OpenWorm clean] output dir: {outdir}")
    print(f"[OpenWorm clean] objects: {len(rows)}")
    print(f"[OpenWorm clean] options: {json.dumps(opts, indent=2)}")

    for i, row in enumerate(rows, 1):
        in_path = row.get("stl_path") or row.get("cleaned_stl_path")
        if not in_path:
            print(f"[ERROR] row has no stl_path: {row}")
            continue
        name = row.get("object_name") or row.get("safe_name") or os.path.splitext(os.path.basename(in_path))[0]
        safe = row.get("safe_name") or os.path.splitext(os.path.basename(in_path))[0]
        out_path = os.path.join(stldir, safe + ".stl")
        status = "ok"
        err = ""
        try:
            obj = import_stl(in_path)
            obj.name = safe
            before = mesh_stats(obj)
            cleanup_object(obj, opts)
            after = mesh_stats(obj)
            export_selected_stl(obj, out_path)
        except Exception as e:
            status = "error"
            err = repr(e)
            before = {}
            after = {}
            out_path = ""
            print(f"[ERROR] {name}: {err}")

        out = dict(row)
        out.update({
            "clean_status": status,
            "clean_error": err,
            "cleaned_stl_path": out_path,
        })
        for k, v in before.items():
            out[f"before_{k}"] = v
        for k, v in after.items():
            out[f"after_{k}"] = v
        if before and after:
            out["delta_vertices"] = after["vertices"] - before["vertices"]
            out["delta_faces"] = after["faces"] - before["faces"]
            out["delta_boundary_edges"] = after["boundary_edges"] - before["boundary_edges"]
            out["delta_nonmanifold_edges"] = after["nonmanifold_edges"] - before["nonmanifold_edges"]
            out["delta_degenerate_faces"] = after["degenerate_faces"] - before["degenerate_faces"]

        cleaned_rows.append(out)
        if i % 25 == 0 or i == len(rows):
            print(f"[OpenWorm clean] {i}/{len(rows)} objects processed")

    out_manifest = os.path.join(outdir, "openworm_object_stl_manifest_cleaned.csv")
    # Stable field order: original columns + new columns.
    fieldnames = []
    for r in cleaned_rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)
    with open(out_manifest, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(cleaned_rows)

    summary = {
        "input_manifest": manifest,
        "output_manifest": out_manifest,
        "output_stl_dir": stldir,
        "object_count": len(cleaned_rows),
        "error_count": sum(1 for r in cleaned_rows if r.get("clean_status") != "ok"),
        "merge_distance": opts["merge_distance"],
        "degenerate_threshold": opts["degenerate_threshold"],
        "fill_holes_max_sides": opts["fill_holes_max_sides"],
        "elapsed_seconds": time.time() - t0,
        "notes": "Cleaned STLs preserve world/model coordinates. Use the cleaned manifest in the Geant4 validator. Do not recenter STLs independently."
    }
    with open(os.path.join(outdir, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[OpenWorm clean] wrote {out_manifest}")
    print(f"[OpenWorm clean] errors: {summary['error_count']}")
    print(f"[OpenWorm clean] elapsed: {summary['elapsed_seconds']:.1f} s")


if __name__ == "__main__":
    main()
