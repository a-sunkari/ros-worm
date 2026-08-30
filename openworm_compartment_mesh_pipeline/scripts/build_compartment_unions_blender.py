#!/usr/bin/env python3
"""Build aggregate compartment STL candidates from per-object STLs using Blender.

Methods:
  join          : import objects, join meshes, clean/export. This is for visual/reference only; not a boolean union.
  boolean_union : sequential Blender Boolean UNION with EXACT solver. Use only after tests; can fail or alter anatomy.
"""
import argparse, json, csv, os, re, math
from pathlib import Path
import bpy
from mathutils import Vector


def parse_args():
    import sys
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--')+1:]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--groups', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--compartments', required=True, help='comma list of group names')
    ap.add_argument('--method', choices=['join','boolean_union'], default='join')
    ap.add_argument('--max-objects-per-compartment', type=int, default=-1)
    return ap.parse_args(argv)


def safe_name(s):
    return re.sub(r'[^A-Za-z0-9_]+','_',s)


def import_stl(path):
    # clear selection before import
    bpy.ops.object.select_all(action='DESELECT')
    if hasattr(bpy.ops.wm, 'stl_import'):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    if not objs:
        raise RuntimeError(f'No mesh imported from {path}')
    # STL import may create one object
    return objs[0]


def export_stl(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if hasattr(bpy.ops.wm, 'stl_export'):
        try:
            bpy.ops.wm.stl_export(filepath=str(path), export_selected_objects=True, apply_modifiers=True, ascii_format=False)
            return
        except Exception as e:
            print('[WARN] wm.stl_export failed:', repr(e))
    bpy.ops.export_mesh.stl(filepath=str(path), use_selection=True, use_mesh_modifiers=True, ascii=False)


def cleanup_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try: bpy.ops.mesh.remove_doubles(threshold=1e-8)
    except Exception: pass
    try: bpy.ops.mesh.delete_loose()
    except Exception: pass
    try: bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception: pass
    bpy.ops.object.mode_set(mode='OBJECT')


def bbox(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = [min(c[i] for c in corners) for i in range(3)]
    mx = [max(c[i] for c in corners) for i in range(3)]
    return mn, mx


def load_manifest(path):
    rows = {}
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows[r['object_name']] = r
    return rows


def main():
    args = parse_args()
    outdir = Path(args.outdir)
    rows = load_manifest(args.manifest)
    groups = json.loads(Path(args.groups).read_text())
    comps = [x.strip() for x in args.compartments.split(',') if x.strip()]
    stldir = outdir / 'stl'
    report = []

    # blank scene
    bpy.ops.object.delete()

    for comp in comps:
        names = groups.get(comp, [])
        if args.max_objects_per_compartment > 0:
            names = names[:args.max_objects_per_compartment]
        names = [n for n in names if n in rows]
        print(f"\n[COMPARTMENT] {comp}: {len(names)} objects method={args.method}")
        if not names:
            report.append({'compartment': comp, 'status': 'empty'})
            continue
        # clear scene for each compartment
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        imported = []
        errors = []
        for n in names:
            try:
                obj = import_stl(rows[n]['stl_path'])
                obj.name = safe_name(n)
                imported.append(obj)
            except Exception as e:
                print('[ERROR import]', n, repr(e))
                errors.append(f'{n}: {repr(e)}')

        if not imported:
            report.append({'compartment': comp, 'status': 'all_import_failed', 'errors': '; '.join(errors)})
            continue

        try:
            if args.method == 'join':
                bpy.ops.object.select_all(action='DESELECT')
                for o in imported: o.select_set(True)
                bpy.context.view_layer.objects.active = imported[0]
                bpy.ops.object.join()
                base = bpy.context.object
                base.name = safe_name(comp)
                cleanup_active(base)
            else:
                base = imported[0]
                base.name = safe_name(comp)
                for j, cutter in enumerate(imported[1:], start=2):
                    bpy.context.view_layer.objects.active = base
                    mod = base.modifiers.new(name=f'union_{j}_{cutter.name}', type='BOOLEAN')
                    mod.operation = 'UNION'
                    mod.object = cutter
                    try:
                        mod.solver = 'EXACT'
                    except Exception:
                        pass
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        bpy.data.objects.remove(cutter, do_unlink=True)
                    except Exception as e:
                        errors.append(f'boolean failed {base.name} UNION {cutter.name}: {repr(e)}')
                        print('[ERROR boolean]', errors[-1])
                cleanup_active(base)

            outpath = stldir / f'{safe_name(comp)}.stl'
            export_stl(base, outpath)
            mn, mx = bbox(base)
            verts = len(base.data.vertices)
            faces = len(base.data.polygons)
            report.append({'object_name': comp, 'safe_name': safe_name(comp), 'category_guess': comp,
                           'stl_path': str(outpath), 'min_x': mn[0], 'min_y': mn[1], 'min_z': mn[2],
                           'max_x': mx[0], 'max_y': mx[1], 'max_z': mx[2],
                           'vertices': verts, 'faces': faces, 'method': args.method,
                           'source_count': len(names), 'status': 'ok', 'errors': '; '.join(errors)})
            print('[OK]', comp, 'faces=', faces, '->', outpath)
        except Exception as e:
            report.append({'object_name': comp, 'safe_name': safe_name(comp), 'category_guess': comp,
                           'status': 'failed', 'errors': '; '.join(errors + [repr(e)])})
            print('[FAILED]', comp, repr(e))

    # write manifest
    outmanifest = outdir / 'compartment_manifest.csv'
    keys = ['object_name','safe_name','category_guess','stl_path','min_x','min_y','min_z','max_x','max_y','max_z','vertices','faces','method','source_count','status','errors']
    with open(outmanifest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in report:
            w.writerow({k: r.get(k,'') for k in keys})
    print('\nWrote', outmanifest)

if __name__ == '__main__':
    main()
