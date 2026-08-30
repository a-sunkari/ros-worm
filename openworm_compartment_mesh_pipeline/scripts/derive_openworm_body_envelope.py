#!/usr/bin/env python3
"""
Derive a filled whole-body external contour mesh from OpenWorm shell-like meshes
(e.g. Cuticle/hyp7), producing a Geant4 parent volume candidate.

This does NOT boolean internal anatomy. It builds a smooth, watertight tube-like
outer envelope from the outer radial extent of selected source meshes along the
worm long axis (default: y). This is intended to create the 'whole body' parent
volume when Cuticle itself is a thin shell material and contains() tests fail.
"""
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import trimesh


def load_mesh_for_name(df, name):
    rows = df[df["object_name"] == name]
    if rows.empty:
        raise ValueError(f"Object not found in manifest: {name}")
    path = Path(rows.iloc[0]["stl_path"])
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    if mesh.vertices.size == 0:
        raise ValueError(f"Empty mesh for {name}: {path}")
    return mesh, path


def moving_average_closed(arr, window):
    if window <= 1:
        return arr
    window = int(window)
    pad = window // 2
    kernel = np.ones(window) / window
    padded = np.concatenate([arr[-pad:], arr, arr[:pad]]) if pad else arr
    return np.convolve(padded, kernel, mode="valid")[:len(arr)]


def smooth_open(arr, window):
    if window <= 1:
        return arr
    window = int(window)
    pad = window // 2
    kernel = np.ones(window) / window
    padded = np.pad(arr, (pad, pad), mode="edge")
    return np.convolve(padded, kernel, mode="valid")[:len(arr)]


def build_envelope(points, ny=240, ntheta=96, percentile=99.5,
                   pad_y_frac=0.002, radial_pad=0.0, smooth_theta=5, smooth_y=5,
                   min_points_per_slice=20):
    # Coordinate convention from your OpenWorm files: y is long axis, x/z transverse.
    y_min, y_max = points[:,1].min(), points[:,1].max()
    y_pad = (y_max - y_min) * pad_y_frac
    y_edges = np.linspace(y_min - y_pad, y_max + y_pad, ny + 1)
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    theta_edges = np.linspace(-math.pi, math.pi, ntheta + 1)
    theta_centers = 0.5 * (theta_edges[:-1] + theta_edges[1:])

    centers = np.zeros((ny, 2), dtype=float)  # x,z center per slice
    radii = np.zeros((ny, ntheta), dtype=float)
    valid = np.zeros(ny, dtype=bool)

    last_center = np.median(points[:, [0,2]], axis=0)
    global_r = np.percentile(np.linalg.norm(points[:,[0,2]] - last_center, axis=1), percentile)

    for i in range(ny):
        lo, hi = y_edges[i], y_edges[i+1]
        sl = points[(points[:,1] >= lo) & (points[:,1] < hi)]
        if len(sl) < min_points_per_slice:
            centers[i] = last_center
            radii[i] = global_r
            continue
        c = np.median(sl[:, [0,2]], axis=0)
        last_center = c
        centers[i] = c
        dx = sl[:,0] - c[0]
        dz = sl[:,2] - c[1]
        theta = np.arctan2(dz, dx)
        r = np.sqrt(dx*dx + dz*dz)
        # Fill each theta bin with high-percentile radial extent.
        rr = np.zeros(ntheta)
        for j in range(ntheta):
            mask = (theta >= theta_edges[j]) & (theta < theta_edges[j+1])
            if np.any(mask):
                rr[j] = np.percentile(r[mask], percentile)
            else:
                # fallback: nearest angular samples
                d = np.abs(np.angle(np.exp(1j*(theta - theta_centers[j]))))
                k = min(max(5, len(r)//100), len(r))
                nearest = np.argpartition(d, k-1)[:k]
                rr[j] = np.percentile(r[nearest], percentile)
        rr = moving_average_closed(rr, smooth_theta)
        radii[i] = rr + radial_pad
        valid[i] = True

    # Interpolate/smooth centers and radii along y.
    for col in range(2):
        centers[:, col] = smooth_open(centers[:, col], smooth_y)
    for j in range(ntheta):
        radii[:, j] = smooth_open(radii[:, j], smooth_y)

    verts = []
    for i, y in enumerate(y_centers):
        cx, cz = centers[i]
        for j, th in enumerate(theta_centers):
            rr = max(radii[i, j], 1e-9)
            verts.append([cx + rr * math.cos(th), y, cz + rr * math.sin(th)])
    verts = np.asarray(verts, dtype=float)

    faces = []
    # side quads as triangles
    for i in range(ny - 1):
        for j in range(ntheta):
            a = i*ntheta + j
            b = i*ntheta + ((j+1) % ntheta)
            c = (i+1)*ntheta + j
            d = (i+1)*ntheta + ((j+1) % ntheta)
            faces.append([a, c, b])
            faces.append([b, c, d])
    # end caps
    start_center_idx = len(verts)
    end_center_idx = len(verts) + 1
    verts = np.vstack([verts, [centers[0,0], y_centers[0], centers[0,1]], [centers[-1,0], y_centers[-1], centers[-1,1]]])
    # cap winding chosen; fix_normals later will correct if needed
    for j in range(ntheta):
        a = j
        b = (j+1) % ntheta
        faces.append([start_center_idx, b, a])
        a2 = (ny-1)*ntheta + j
        b2 = (ny-1)*ntheta + ((j+1) % ntheta)
        faces.append([end_center_idx, a2, b2])

    mesh = trimesh.Trimesh(vertices=verts, faces=np.asarray(faces), process=True)
    trimesh.repair.fix_normals(mesh)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--sources", default="Cuticle,hyp7", help="comma-separated source objects")
    ap.add_argument("--ny", type=int, default=240)
    ap.add_argument("--ntheta", type=int, default=96)
    ap.add_argument("--percentile", type=float, default=99.5)
    ap.add_argument("--radial-pad", type=float, default=0.0, help="pad radius in model units")
    ap.add_argument("--smooth-theta", type=int, default=5)
    ap.add_argument("--smooth-y", type=int, default=5)
    args = ap.parse_args()

    manifest = Path(args.manifest)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(manifest)

    src_names = [s.strip() for s in args.sources.split(',') if s.strip()]
    all_vertices = []
    src_info = []
    for name in src_names:
        mesh, path = load_mesh_for_name(df, name)
        all_vertices.append(np.asarray(mesh.vertices))
        src_info.append({"name": name, "path": str(path), "verts": int(len(mesh.vertices)), "faces": int(len(mesh.faces)), "bounds": mesh.bounds.tolist(), "watertight": bool(mesh.is_watertight), "volume": float(mesh.volume)})
    pts = np.vstack(all_vertices)

    env = build_envelope(pts, ny=args.ny, ntheta=args.ntheta, percentile=args.percentile,
                         radial_pad=args.radial_pad, smooth_theta=args.smooth_theta, smooth_y=args.smooth_y)
    out_stl = outdir / "whole_body_envelope.stl"
    env.export(out_stl)
    meta = {
        "output_stl": str(out_stl),
        "sources": src_info,
        "ny": args.ny,
        "ntheta": args.ntheta,
        "percentile": args.percentile,
        "radial_pad_model_units": args.radial_pad,
        "smooth_theta": args.smooth_theta,
        "smooth_y": args.smooth_y,
        "envelope_vertices": int(len(env.vertices)),
        "envelope_faces": int(len(env.faces)),
        "envelope_watertight": bool(env.is_watertight),
        "envelope_volume": float(env.volume),
        "envelope_bounds": env.bounds.tolist(),
        "source_point_bounds": [pts.min(axis=0).tolist(), pts.max(axis=0).tolist()],
    }
    (outdir / "whole_body_envelope_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
