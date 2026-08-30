#!/usr/bin/env python3
"""Minimal STL sanity checker for the OpenWorm outer-body mesh.

This intentionally avoids extra dependencies. It checks standard binary STL
files, reports triangle count, bounding box, scale factor to a target length,
and an edge-manifold proxy check. It is not a full CAD validator, but it catches
common problems before using a tessellated solid in Geant4.
"""
from __future__ import annotations

import argparse
import struct
from collections import defaultdict
from pathlib import Path


def read_binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("file is smaller than a binary STL header")
    ntri = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + ntri * 50
    if expected != len(data):
        raise ValueError(
            f"not a standard binary STL: expected {expected} bytes from triangle count, got {len(data)}"
        )
    tris = []
    off = 84
    for _ in range(ntri):
        off += 12  # normal
        tri = []
        for _ in range(3):
            tri.append(struct.unpack_from("<fff", data, off))
            off += 12
        off += 2
        tris.append(tuple(tri))
    return tris


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", type=Path)
    ap.add_argument("--target-length-mm", type=float, default=1.0)
    ap.add_argument("--round-digits", type=int, default=7)
    args = ap.parse_args()

    tris = read_binary_stl(args.stl)
    verts = [v for tri in tris for v in tri]
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    spans = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]
    longest = max(spans)
    shortest = min(spans)
    scale = args.target_length_mm / longest if longest > 0 else float("nan")

    edges = defaultdict(int)
    for tri in tris:
        pts = [tuple(round(c, args.round_digits) for c in v) for v in tri]
        for a, b in [(pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0])]:
            edges[tuple(sorted((a, b)))] += 1

    boundary = sum(1 for c in edges.values() if c == 1)
    nonmanifold = sum(1 for c in edges.values() if c > 2)
    two_face = sum(1 for c in edges.values() if c == 2)

    print("STL mesh check")
    print("--------------")
    print(f"file:                 {args.stl}")
    print(f"size MB:              {args.stl.stat().st_size / 1024 / 1024:.3f}")
    print(f"triangles:            {len(tris)}")
    print(f"vertices in triangles:{len(verts)}")
    print(f"bbox x span:          {spans[0]:.8g}")
    print(f"bbox y span:          {spans[1]:.8g}")
    print(f"bbox z span:          {spans[2]:.8g}")
    print(f"longest dimension:    {longest:.8g}")
    print(f"shortest dimension:   {shortest:.8g}")
    print(f"aspect ratio:         {longest / shortest if shortest > 0 else float('inf'):.5g}")
    print(f"scale to {args.target_length_mm:g} mm: {scale:.8g} mm/model-unit")
    print()
    print("Edge manifold proxy check")
    print(f"unique edges:          {len(edges)}")
    print(f"2-face edges:          {two_face}")
    print(f"boundary/open edges:   {boundary}")
    print(f"nonmanifold edges:     {nonmanifold}")
    if boundary == 0 and nonmanifold == 0:
        print("status:                likely closed/watertight")
    else:
        print("status:                has open/nonmanifold edges; test Geant4 navigation carefully")


if __name__ == "__main__":
    main()
