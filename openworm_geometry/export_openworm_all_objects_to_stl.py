#!/usr/bin/env python3
"""
Blender batch exporter for Virtual Worm/OpenWorm anatomy.
Exports every mesh object as its own binary STL in WORLD coordinates, plus CSV/JSON manifests.
Run inside Blender, e.g.:
  blender Virtual_Worm_February_2012.blend --background --python export_openworm_all_objects_to_stl.py -- /home/asunkari/ros-worm/openworm_geometry/object_stls
"""
import bpy, sys, os, re, csv, json, math, struct
from mathutils import Vector

DEGENERATE_AREA_EPS = 1e-18  # model-unit^2; intentionally tiny, mainly removes zero-area facets
SKIP_NAMES = {"1um", "10um", "100um", "1mm"}


def argv_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def safe_name(name):
    s = re.sub(r"[^A-Za-z0-9_.+-]+", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unnamed"


def tri_area(a, b, c):
    return 0.5 * ((b - a).cross(c - a)).length


def write_binary_stl(path, name, triangles):
    header = ("OpenWorm object %s" % name).encode("ascii", "ignore")[:80]
    header = header + b" " * (80 - len(header))
    with open(path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            n = (b - a).cross(c - a)
            if n.length > 0:
                n.normalize()
            else:
                n = Vector((0, 0, 0))
            f.write(struct.pack("<12fH",
                float(n.x), float(n.y), float(n.z),
                float(a.x), float(a.y), float(a.z),
                float(b.x), float(b.y), float(b.z),
                float(c.x), float(c.y), float(c.z),
                0))


def category_guess(name):
    n = name.lower()
    if n in {"cuticle"}: return "cuticle/body-envelope"
    if n.startswith("hyp") or "seam" in n: return "hypodermis/seam"
    if n.startswith("int"): return "intestine"
    if n.startswith("mu_bod") or n.startswith("vm") or n.startswith("um") or n.startswith("pm") or n.startswith("mc"):
        return "muscle/pharynx-muscle"
    if "gonad" in n or "oocyte" in n or "spermat" in n or "rachis" in n or n.startswith("ut") or "vul" in n:
        return "reproductive"
    if "can" in n or "excret" in n: return "excretory/canal"
    if n.endswith("l") or n.endswith("r") or re.match(r"^(a|b|c|d|i|m|p|r|s|v)[a-z]{1,4}[dlrv]?$", n):
        return "neuron-or-cell"
    return "other-cell/anatomy"


def main():
    args = argv_after_dash()
    outdir = args[0] if args else os.path.abspath("openworm_object_stls")
    os.makedirs(outdir, exist_ok=True)
    stldir = os.path.join(outdir, "stl")
    os.makedirs(stldir, exist_ok=True)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    global_min = Vector((math.inf, math.inf, math.inf))
    global_max = Vector((-math.inf, -math.inf, -math.inf))

    mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name not in SKIP_NAMES]
    print(f"[OpenWorm export] Exporting {len(mesh_objs)} mesh objects to {stldir}")

    used = {}
    for idx, obj in enumerate(mesh_objs, 1):
        base = safe_name(obj.name)
        used[base] = used.get(base, 0) + 1
        fname = base if used[base] == 1 else f"{base}_{used[base]}"
        stl_path = os.path.join(stldir, fname + ".stl")

        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mesh.calc_loop_triangles()
        mw = eval_obj.matrix_world.copy()

        triangles = []
        raw_tri_count = 0
        skipped_degenerate = 0
        mn = Vector((math.inf, math.inf, math.inf))
        mx = Vector((-math.inf, -math.inf, -math.inf))

        verts_world = [mw @ v.co for v in mesh.vertices]
        for tri in mesh.loop_triangles:
            raw_tri_count += 1
            a, b, c = (verts_world[i] for i in tri.vertices)
            area = tri_area(a, b, c)
            if area <= DEGENERATE_AREA_EPS:
                skipped_degenerate += 1
                continue
            triangles.append((a, b, c))
            for p in (a, b, c):
                mn.x = min(mn.x, p.x); mn.y = min(mn.y, p.y); mn.z = min(mn.z, p.z)
                mx.x = max(mx.x, p.x); mx.y = max(mx.y, p.y); mx.z = max(mx.z, p.z)
                global_min.x = min(global_min.x, p.x); global_min.y = min(global_min.y, p.y); global_min.z = min(global_min.z, p.z)
                global_max.x = max(global_max.x, p.x); global_max.y = max(global_max.y, p.y); global_max.z = max(global_max.z, p.z)

        eval_obj.to_mesh_clear()
        if not triangles:
            print(f"[WARN] {obj.name}: no valid triangles after degenerate removal; skipping STL write")
            continue

        write_binary_stl(stl_path, obj.name, triangles)
        span = mx - mn
        rows.append({
            "object_name": obj.name,
            "safe_name": fname,
            "category_guess": category_guess(obj.name),
            "stl_path": stl_path,
            "raw_triangles": raw_tri_count,
            "exported_triangles": len(triangles),
            "skipped_degenerate": skipped_degenerate,
            "min_x": mn.x, "min_y": mn.y, "min_z": mn.z,
            "max_x": mx.x, "max_y": mx.y, "max_z": mx.z,
            "span_x": span.x, "span_y": span.y, "span_z": span.z,
        })
        if idx % 50 == 0:
            print(f"[OpenWorm export] {idx}/{len(mesh_objs)} objects...")

    csv_path = os.path.join(outdir, "openworm_object_stl_manifest.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

    meta = {
        "object_count": len(rows),
        "global_min": [global_min.x, global_min.y, global_min.z],
        "global_max": [global_max.x, global_max.y, global_max.z],
        "global_span": [(global_max-global_min).x, (global_max-global_min).y, (global_max-global_min).z],
        "degenerate_area_eps_model_units2": DEGENERATE_AREA_EPS,
        "notes": "STLs are exported in Blender world/model coordinates. Do not recenter each STL independently in Geant4; use one common global center/scale for all objects."
    }
    json_path = os.path.join(outdir, "openworm_scene_geometry_meta.json")
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[OpenWorm export] Wrote {csv_path}")
    print(f"[OpenWorm export] Wrote {json_path}")
    print(f"[OpenWorm export] Global span = {meta['global_span']} model units")

if __name__ == "__main__":
    main()
