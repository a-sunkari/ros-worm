#!/usr/bin/env python3
# Compatibility helper for old stage1 pipeline: pass entries id:name:path.csv and merge with region metadata.
import argparse, csv
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('entries',nargs='*'); args=ap.parse_args()
rows=[]
for e in args.entries:
    rid,name,path=e.split(':',2)
    p=Path(path)
    if not p.exists(): continue
    with open(p) as f:
        for r in csv.DictReader(f):
            r['region_id']=rid; r['region_key']=name; rows.append(r)
if rows:
    fields=['region_id','region_key']+[k for k in rows[0].keys() if k not in ('region_id','region_key')]
    with open(args.output,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
else:
    Path(args.output).write_text('region_id,region_key\n')
