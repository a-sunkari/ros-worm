"""
OpenWorm / anatomical mesh readiness audit for Blender.

Run inside Blender:
  blender Virtual_Worm_February_2012.blend --background --python openworm_blender_geometry_audit.py

Outputs next to the .blend by default, or change OUT_DIR below.

What it checks:
  - per-object vertex/face/edge counts
  - boundary edges: edges used by exactly 1 face; open mesh / holes
  - nonmanifold edges: edges used by != 2 faces
  - degenerate faces: tiny/zero-area polygons
  - bounding boxes and extents
  - AABB-overlap object pairs
  - optional BVH triangle-overlap candidate pairs for AABB candidates

Important:
  BVH overlap is a practical triage signal, not a final Geant4 truth. It finds triangle-level BVH overlaps, then you still validate the exported GDML in Geant4 with CheckOverlaps().
"""

import bpy
import bmesh
import csv
import os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# ---------------- USER SETTINGS ----------------
OUT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()
AREA_EPS = 1e-12
RUN_BVH_PAIR_SCAN = True
MAX_AABB_PAIRS_FOR_BVH = 50000  # safety cap; raise if needed
CREATE_COLLECTIONS = True
# ------------------------------------------------

os.makedirs(OUT_DIR, exist_ok=True)

mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']

# Ensure evaluated depsgraph exists for modifier-aware BVH
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()


def world_bbox(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return mn, mx


def bbox_overlap(a_min, a_max, b_min, b_max):
    return (a_min.x <= b_max.x and a_max.x >= b_min.x and
            a_min.y <= b_max.y and a_max.y >= b_min.y and
            a_min.z <= b_max.z and a_max.z >= b_min.z)


def bbox_intersection_extent(a_min, a_max, b_min, b_max):
    mn = Vector((max(a_min.x, b_min.x), max(a_min.y, b_min.y), max(a_min.z, b_min.z)))
    mx = Vector((min(a_max.x, b_max.x), min(a_max.y, b_max.y), min(a_max.z, b_max.z)))
    return Vector((max(0, mx.x-mn.x), max(0, mx.y-mn.y), max(0, mx.z-mn.z)))


def audit_object(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    boundary_edges = 0
    nonmanifold_edges = 0
    wire_edges = 0
    for e in bm.edges:
        lf = len(e.link_faces)
        if lf == 0:
            wire_edges += 1
        if lf == 1:
            boundary_edges += 1
        if lf != 2:
            nonmanifold_edges += 1

    degenerate_faces = 0
    min_area = None
    for f in bm.faces:
        area = f.calc_area()
        if min_area is None or area < min_area:
            min_area = area
        if area <= AREA_EPS:
            degenerate_faces += 1

    loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
    bm.free()

    mn, mx = world_bbox(obj)
    ext = mx - mn

    return {
        'object': obj.name,
        'verts': len(me.vertices),
        'edges': len(me.edges),
        'polygons': len(me.polygons),
        'boundary_edges': boundary_edges,
        'nonmanifold_edges': nonmanifold_edges,
        'wire_edges': wire_edges,
        'loose_verts': loose_verts,
        'degenerate_faces': degenerate_faces,
        'min_face_area': min_area if min_area is not None else 0,
        'bbox_min_x': mn.x, 'bbox_min_y': mn.y, 'bbox_min_z': mn.z,
        'bbox_max_x': mx.x, 'bbox_max_y': mx.y, 'bbox_max_z': mx.z,
        'extent_x': ext.x, 'extent_y': ext.y, 'extent_z': ext.z,
        'problem_score': boundary_edges + nonmanifold_edges + degenerate_faces + wire_edges + loose_verts,
    }

print(f"Auditing {len(mesh_objs)} mesh objects...")
rows = [audit_object(o) for o in mesh_objs]

report_path = os.path.join(OUT_DIR, 'openworm_blender_mesh_audit.csv')
with open(report_path, 'w', newline='') as f:
    fields = list(rows[0].keys()) if rows else []
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print('Wrote', report_path)

# Create quick diagnostic collections in Blender for interactive review.
if CREATE_COLLECTIONS:
    for cname in ['AUDIT_boundary_or_open', 'AUDIT_nonmanifold', 'AUDIT_degenerate', 'AUDIT_cleanish']:
        if cname not in bpy.data.collections:
            bpy.context.scene.collection.children.link(bpy.data.collections.new(cname))

    row_by_name = {r['object']: r for r in rows}
    for obj in mesh_objs:
        r = row_by_name[obj.name]
        if r['nonmanifold_edges'] > 0:
            target = bpy.data.collections['AUDIT_nonmanifold']
        elif r['boundary_edges'] > 0 or r['wire_edges'] > 0 or r['loose_verts'] > 0:
            target = bpy.data.collections['AUDIT_boundary_or_open']
        elif r['degenerate_faces'] > 0:
            target = bpy.data.collections['AUDIT_degenerate']
        else:
            target = bpy.data.collections['AUDIT_cleanish']
        if obj.name not in target.objects:
            target.objects.link(obj)

# AABB pair scan
boxes = []
obj_by_name = {o.name: o for o in mesh_objs}
for obj in mesh_objs:
    mn, mx = world_bbox(obj)
    boxes.append((obj.name, mn, mx))

aabb_pairs = []
for i in range(len(boxes)):
    name_a, amin, amax = boxes[i]
    for j in range(i + 1, len(boxes)):
        name_b, bmin, bmax = boxes[j]
        if bbox_overlap(amin, amax, bmin, bmax):
            ext = bbox_intersection_extent(amin, amax, bmin, bmax)
            vol = ext.x * ext.y * ext.z
            aabb_pairs.append((vol, name_a, name_b, ext.x, ext.y, ext.z))

aabb_pairs.sort(reverse=True)
aabb_path = os.path.join(OUT_DIR, 'openworm_aabb_overlap_candidates.csv')
with open(aabb_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['bbox_intersection_volume', 'object_a', 'object_b', 'extent_x', 'extent_y', 'extent_z'])
    w.writerows(aabb_pairs)
print('Wrote', aabb_path, 'pairs:', len(aabb_pairs))

# BVH pair scan on top AABB candidates. This is still a candidate test, but much better than boxes alone.
if RUN_BVH_PAIR_SCAN:
    bvh_cache = {}

    def get_bvh(obj):
        if obj.name in bvh_cache:
            return bvh_cache[obj.name]
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        try:
            bvh = BVHTree.FromMesh(mesh, epsilon=0.0)
        finally:
            eval_obj.to_mesh_clear()
        bvh_cache[obj.name] = bvh
        return bvh

    bvh_hits = []
    scan_pairs = aabb_pairs[:MAX_AABB_PAIRS_FOR_BVH]
    print(f'Running BVH overlap candidate scan on {len(scan_pairs)} AABB pairs...')
    for k, (_vol, a, b, ex, ey, ez) in enumerate(scan_pairs, 1):
        if k % 1000 == 0:
            print('  BVH pair', k, '/', len(scan_pairs))
        oa = obj_by_name.get(a)
        ob = obj_by_name.get(b)
        if oa is None or ob is None:
            continue
        try:
            hits = get_bvh(oa).overlap(get_bvh(ob))
        except Exception as e:
            bvh_hits.append(('ERROR', a, b, ex, ey, ez, str(e)))
            continue
        if hits:
            bvh_hits.append((len(hits), a, b, ex, ey, ez, ''))

    bvh_hits.sort(key=lambda x: (x[0] if isinstance(x[0], int) else -1), reverse=True)
    bvh_path = os.path.join(OUT_DIR, 'openworm_bvh_overlap_candidates.csv')
    with open(bvh_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['bvh_overlap_pair_count', 'object_a', 'object_b', 'bbox_extent_x', 'bbox_extent_y', 'bbox_extent_z', 'error'])
        w.writerows(bvh_hits)
    print('Wrote', bvh_path, 'BVH-hit pairs:', len(bvh_hits))

print('Done.')
