import bpy
from pathlib import Path

src = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl")
outdir = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/baked_priority_meshes_test/voxel_remesh_nervous")
outdir.mkdir(exist_ok=True)

voxel_size = 0.03
out = outdir / f"NervousSystem_baked_union_voxel_{voxel_size:.3f}.stl"

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def import_stl(path, name):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path))
    after = set(bpy.data.objects)
    imported = list(after - before)

    if not imported:
        imported = [bpy.context.object]

    bpy.ops.object.select_all(action="DESELECT")
    for obj in imported:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]

    if len(imported) > 1:
        bpy.ops.object.join()

    obj = bpy.context.object
    obj.name = name
    obj.data = obj.data.copy()
    obj.data.name = name + "_mesh_single_user"
    return obj

def cleanup_obj(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if obj.data.users > 1:
        obj.data = obj.data.copy()

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    try:
        bpy.ops.mesh.merge_by_distance(distance=1e-6)
    except Exception:
        pass

    try:
        bpy.ops.mesh.delete_loose()
    except Exception:
        pass

    try:
        bpy.ops.mesh.normals_make_consistent(inside=False)
    except Exception:
        pass

    bpy.ops.object.mode_set(mode="OBJECT")

def export_stl(obj, out):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    try:
        bpy.ops.wm.stl_export(filepath=str(out), export_selected_objects=True)
        return
    except Exception as e:
        print("[EXPORT_FALLBACK] wm.stl_export failed:", repr(e))

    try:
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
    except Exception:
        pass

    bpy.ops.export_mesh.stl(filepath=str(out), use_selection=True, ascii=False)

clear_scene()
print("[IMPORT]", src)
obj = import_stl(src, "NervousSystem")
cleanup_obj(obj)

remesh = obj.modifiers.new(name="NervousVoxelRemesh", type="REMESH")
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
export_stl(obj, out)

print("[WROTE]", out)
