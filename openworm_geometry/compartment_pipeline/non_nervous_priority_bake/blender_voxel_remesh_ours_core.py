import bpy
import csv
from pathlib import Path

base = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/non_nervous_priority_bake")
src_manifest = base / "debug_core_resolved_flat_simple_body_manifest.csv"
outdir = base / "voxel_remesh_wu_like"
outdir.mkdir(exist_ok=True)

voxel_size = 0.02

remesh_categories = {
    "DigestiveSystem",
    "ReproductiveSystem",
    "ExcretorySystem",
    "BodyWallMuscle",
}

with src_manifest.open(newline="") as f:
    rows = list(csv.DictReader(f))
    fieldnames = rows[0].keys()

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def import_stl(path, name):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path))
    after = set(bpy.data.objects)
    imported = list(after - before)

    if not imported:
        obj = bpy.context.object
        imported = [obj]

    # If STL import created multiple objects, join them into one.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in imported:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]

    if len(imported) > 1:
        bpy.ops.object.join()

    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_mesh_single_user"

    # Critical: make mesh datablock single-user so transform_apply/modifier_apply works.
    obj.data = obj.data.copy()
    obj.data.name = name + "_mesh_single_user_copy"

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return obj

def cleanup_obj(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Ensure object owns its mesh datablock before applying transforms/modifiers.
    if obj.data.users > 1:
        obj.data = obj.data.copy()
        obj.data.name = obj.name + "_mesh_single_user_cleanup"

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    # Blender 4.x uses merge_by_distance, older versions used remove_doubles.
    try:
        bpy.ops.mesh.merge_by_distance(distance=1e-6)
    except Exception:
        try:
            bpy.ops.mesh.remove_doubles(threshold=1e-6)
        except Exception as e:
            print("[WARN] merge/remove doubles skipped:", e)

    try:
        bpy.ops.mesh.delete_loose()
    except Exception as e:
        print("[WARN] delete loose skipped:", e)

    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception as e:
        print("[WARN] normal consistency skipped:", e)

    bpy.ops.object.mode_set(mode="OBJECT")

def voxel_remesh(obj, voxel_size):
    cleanup_obj(obj)

    remesh = obj.modifiers.new(name="G4VoxelRemesh", type="REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = voxel_size
    remesh.adaptivity = 0.0
    remesh.use_smooth_shade = False

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    cleanup_obj(obj)

    dec = obj.modifiers.new(name="LightDecimate", type="DECIMATE")
    dec.ratio = 0.65
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=dec.name)

    cleanup_obj(obj)

def export_stl(obj, out):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Do NOT use hasattr() on bpy.ops; it can lie because ops are dynamic.
    # Try Blender 4.1+ operator first, then Blender 4.0 legacy STL add-on.
    try:
        print("[EXPORT_TRY] bpy.ops.wm.stl_export", out)
        bpy.ops.wm.stl_export(filepath=str(out), export_selected_objects=True)
        return
    except Exception as e:
        print("[EXPORT_FALLBACK] wm.stl_export failed:", repr(e))

    try:
        print("[ENABLE_ADDON] io_mesh_stl")
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
    except Exception as e:
        print("[WARN] addon_enable io_mesh_stl failed or unnecessary:", repr(e))

    try:
        print("[EXPORT_TRY] bpy.ops.export_mesh.stl", out)
        bpy.ops.export_mesh.stl(filepath=str(out), use_selection=True, ascii=False)
        return
    except Exception as e:
        print("[EXPORT_FAIL] export_mesh.stl failed:", repr(e))
        raise

new_rows = []

for row in rows:
    cat = row["category_guess"]
    safe = row["safe_name"]
    src = Path(row["stl_path"])

    if cat not in remesh_categories:
        print("[KEEP]", cat, src)
        new_rows.append(row)
        continue

    print("[REMESH_BEGIN]", cat, src)
    clear_scene()
    obj = import_stl(src, safe)
    voxel_remesh(obj, voxel_size)

    out = outdir / f"{safe}_voxel_{voxel_size:.3f}.stl"
    export_stl(obj, out)

    row = dict(row)
    row["stl_path"] = str(out)
    new_rows.append(row)

    print("[WROTE]", cat, out)

out_manifest = base / "debug_core_simple_body_voxel_remesh_children_manifest.csv"

with out_manifest.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_rows)

print("[MANIFEST]", out_manifest)
