#!/usr/bin/env python3
"""
Visual sanity-check for object-preserving OpenWorm STL exports.
Run:
  blender --python preview_openworm_object_stls_in_blender.py -- /path/openworm_object_stl_manifest.csv all
or:
  blender --python preview_openworm_object_stls_in_blender.py -- /path/openworm_object_stl_manifest.csv neuron-or-cell

It imports the per-object STL files in their existing world coordinates, colors by category_guess,
and creates collections by category. It does NOT recenter individual objects.
"""
import bpy, sys, csv, os, math
from mathutils import Vector

COLORS = {
    "cuticle/body-envelope": (0.8, 0.8, 0.9, 0.25),
    "hypodermis/seam":       (0.2, 0.8, 0.8, 0.45),
    "intestine":             (0.9, 0.6, 0.2, 0.65),
    "muscle/pharynx-muscle": (0.9, 0.2, 0.2, 0.60),
    "reproductive":          (0.8, 0.2, 0.8, 0.60),
    "excretory/canal":       (0.2, 0.4, 1.0, 0.70),
    "neuron-or-cell":        (0.1, 1.0, 0.1, 0.80),
    "other-cell/anatomy":    (1.0, 1.0, 0.2, 0.55),
}

def argv_after_dash():
    return sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def mat_for(cat):
    name = "cat_" + cat.replace('/', '_').replace(' ', '_')
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = COLORS.get(cat, (0.7,0.7,0.7,0.6))
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Alpha'].default_value = mat.diffuse_color[3]
        bsdf.inputs['Base Color'].default_value = mat.diffuse_color
    mat.blend_method = 'BLEND'
    mat.use_screen_refraction = True
    return mat

def import_stl(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    after = set(bpy.data.objects)
    new = list(after - before)
    return new[0] if new else bpy.context.object

def main():
    args = argv_after_dash()
    if not args:
        print("Usage: blender --python preview_openworm_object_stls_in_blender.py -- manifest.csv [all|category] [max_objects]")
        return
    manifest = args[0]
    category_filter = args[1] if len(args) > 1 else "all"
    max_objects = int(args[2]) if len(args) > 2 else -1

    clear_scene()
    with open(manifest, newline='') as f:
        rows = list(csv.DictReader(f))
    if category_filter != "all":
        rows = [r for r in rows if r.get('category_guess') == category_filter]
    if max_objects > 0:
        rows = rows[:max_objects]

    collections = {}
    imported = []
    for i, r in enumerate(rows, 1):
        cat = r.get('category_guess', 'other')
        if cat not in collections:
            col = bpy.data.collections.new(cat)
            bpy.context.scene.collection.children.link(col)
            collections[cat] = col
        path = r['stl_path']
        if not os.path.exists(path):
            print(f"[MISSING] {path}")
            continue
        obj = import_stl(path)
        obj.name = r['object_name']
        obj.data.name = r['safe_name'] + "_mesh"
        obj.data.materials.append(mat_for(cat))
        for c in obj.users_collection:
            c.objects.unlink(obj)
        collections[cat].objects.link(obj)
        imported.append(obj)
        if i % 50 == 0:
            print(f"Imported {i}/{len(rows)}")

    # Add an origin marker and set reasonable view clipping/camera
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
    bpy.context.object.name = "world_origin_marker"

    # Compute bounds
    if imported:
        mins = Vector((math.inf, math.inf, math.inf)); maxs = Vector((-math.inf, -math.inf, -math.inf))
        for obj in imported:
            for corner in obj.bound_box:
                p = obj.matrix_world @ Vector(corner)
                mins.x=min(mins.x,p.x); mins.y=min(mins.y,p.y); mins.z=min(mins.z,p.z)
                maxs.x=max(maxs.x,p.x); maxs.y=max(maxs.y,p.y); maxs.z=max(maxs.z,p.z)
        center = (mins+maxs)/2; span = maxs-mins
        bpy.ops.object.light_add(type='AREA', location=(center.x, center.y-20, center.z+20))
        bpy.context.object.data.energy = 600
        bpy.context.object.data.size = 5
        bpy.ops.object.camera_add(location=(center.x, center.y-1.8*max(span.y,1), center.z+0.8*max(span.z,1)), rotation=(math.radians(65), 0, 0))
        bpy.context.scene.camera = bpy.context.object
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.clip_end = 100000

    print(f"Imported {len(imported)} objects. Use Outliner collections to toggle categories.")

if __name__ == '__main__':
    main()
