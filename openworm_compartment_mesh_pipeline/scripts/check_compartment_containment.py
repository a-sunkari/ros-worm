#!/usr/bin/env python3
"""Sample child mesh surface points and test whether they are inside the body STL.
Requires trimesh and usually rtree."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import trimesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--body-stl', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--out-csv', required=True)
    ap.add_argument('--samples-per-object', type=int, default=5000)
    args = ap.parse_args()
    body = trimesh.load(args.body_stl, force='mesh')
    if not body.is_watertight:
        print('[WARN] body mesh is not watertight; contains() may be unreliable')
    df = pd.read_csv(args.manifest)
    rows = []
    for i, r in df.iterrows():
        path = r['stl_path']
        name = r['object_name']
        try:
            m = trimesh.load(path, force='mesh')
            if len(m.faces) == 0:
                raise ValueError('empty mesh')
            n = min(args.samples_per_object, max(50, len(m.faces)))
            pts, face_idx = trimesh.sample.sample_surface(m, n)
            inside = body.contains(pts)
            frac_inside = float(np.mean(inside))
            rows.append({
                'object_name': name,
                'compartment': r.get('compartment', r.get('category_guess','')),
                'samples': n,
                'frac_inside_body': frac_inside,
                'outside_samples': int(np.sum(~inside)),
                'watertight': bool(m.is_watertight),
                'faces': int(len(m.faces)),
                'stl_path': path,
            })
            print(f"[{i+1}/{len(df)}] {name}: inside={frac_inside:.4f} watertight={m.is_watertight}")
        except Exception as e:
            rows.append({'object_name': name, 'error': repr(e), 'stl_path': path})
            print(f"[ERROR] {name}: {e!r}")
    out = pd.DataFrame(rows)
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print('wrote', args.out_csv)

if __name__ == '__main__':
    main()
