#!/usr/bin/env python3
import argparse, re
from pathlib import Path
import pandas as pd

pair_re = re.compile(r"Overlap is detected for volume\s+(ow_(.*?)_phys):(\d+)\s+\(.*?\)\s+with\s+(ow_(.*?)_phys):(\d+)")
depth_re = re.compile(r"overlap at local point .*? by\s+([0-9.eE+-]+)\s+(nm|um|mm)\s+\(max of\s+([0-9]+)\s+cases\)")

def to_um(val, unit):
    v = float(val)
    if unit == 'nm': return v / 1000.0
    if unit == 'um': return v
    if unit == 'mm': return v * 1000.0
    return v

def clean(n):
    if n.startswith('ow_'): n = n[3:]
    if n.endswith('_phys'): n = n[:-5]
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--out-csv', required=True)
    ap.add_argument('--min-depth-um', type=float, default=0.0)
    ap.add_argument('--min-cases', type=int, default=0)
    args = ap.parse_args()
    lines = Path(args.log).read_text(errors='replace').splitlines()
    rows = []
    pending = None
    for line in lines:
        m = pair_re.search(line)
        if m:
            pending = {
                'a_phys': m.group(1), 'a': m.group(2), 'a_copy': int(m.group(3)),
                'b_phys': m.group(4), 'b': m.group(5), 'b_copy': int(m.group(6)),
            }
            continue
        if pending:
            d = depth_re.search(line)
            if d:
                depth_um = to_um(d.group(1), d.group(2))
                cases = int(d.group(3))
                a, b = pending['a'], pending['b']
                key = '||'.join(sorted([a,b]))
                if depth_um >= args.min_depth_um and cases >= args.min_cases:
                    rows.append({**pending, 'pair_key': key, 'depth_um': depth_um, 'cases': cases})
                pending = None
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(['depth_um','cases'], ascending=[False, False])
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out_csv, index=False)
    print(f"parsed rows={len(df)} unique_pairs={df['pair_key'].nunique() if len(df) else 0} -> {args.out_csv}")
    if len(df):
        print(df.head(25).to_string(index=False))

if __name__ == '__main__':
    main()
