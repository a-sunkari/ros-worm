#!/usr/bin/env python3
import argparse, csv, json, math, os
from pathlib import Path

KEV_TO_J = 1.602176634e-16
GY = 1.0

def load_regions(path):
    out = {}
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            out[int(r['region_id'])] = r
    return out

def load_materials(path):
    out = {}
    if not path:
        return out
    p = Path(path)
    if not p.exists():
        return out
    with p.open(newline='') as f:
        for r in csv.DictReader(f):
            try:
                rid = int(r['region_id'])
            except Exception:
                continue
            out[rid] = r
    return out

def find_tree(root_file, preferred):
    import ROOT
    obj = root_file.Get(preferred)
    if obj:
        return obj
    # Geant4 may store ntuples under directories; scan all keys recursively one level.
    for key in root_file.GetListOfKeys():
        o = key.ReadObj()
        if o.InheritsFrom('TDirectory'):
            t = o.Get(preferred)
            if t:
                return t
        elif key.GetName() == preferred:
            return o
    return None

def parse_region_masses(path):
    import re
    masses = {}
    if not path:
        return masses
    pattern = re.compile(r"\[ROS-WORM\]\[REGION\].*?id=(\d+).*?mass_kg=([0-9.eE+-]+)")
    for line in Path(path).read_text(errors='ignore').splitlines():
        match = pattern.search(line)
        if match:
            masses[int(match.group(1))] = float(match.group(2))
    return masses

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root_file')
    ap.add_argument('--regions', required=True)
    ap.add_argument('--materials', default=None, help='Optional region_materials.csv for material/density metadata')
    ap.add_argument('--transport-log', default=None, help='Transport log containing authoritative scoring masses')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--target-dose-rate', type=float, default=1.0)
    ap.add_argument('--pulse-s', type=float, default=10.0)
    ap.add_argument('--bins', type=int, default=80)
    ap.add_argument('--emin-kev', type=float, default=0.05)
    ap.add_argument('--emax-kev', type=float, default=100.0)
    ap.add_argument('--skip-step-csv', action='store_true', help='Do not materialize the large edep_hits.csv table')
    args = ap.parse_args()

    import ROOT
    regions = load_regions(args.regions)
    materials = load_materials(args.materials)
    masses = parse_region_masses(args.transport_log)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    f = ROOT.TFile.Open(args.root_file)
    if not f or f.IsZombie():
        raise SystemExit(f'Could not open ROOT file: {args.root_file}')
    event = find_tree(f, 'event')
    steps = find_tree(f, 'steps')
    secondaries = find_tree(f, 'secondaries')
    if not event:
        raise SystemExit('Could not find event ntuple in ROOT file')

    branch_by_id = {
        1:'Edep_body_keV', 2:'Edep_nervous_keV', 3:'Edep_bodywall_keV',
        4:'Edep_digestive_keV', 5:'Edep_reproductive_keV', 6:'Edep_excretory_keV'
    }
    # Keep aggregation in compiled ROOT code. A Python row loop over a 10M-event
    # tree takes minutes even though the reduction itself is simple.
    rdf = ROOT.RDataFrame(event)
    n_events = int(rdf.Count().GetValue())
    branch_names = {str(x.GetName()) for x in event.GetListOfBranches()}
    edep_by_region = {i:(float(rdf.Sum(b).GetValue()) if b in branch_names else 0.0) for i,b in branch_by_id.items()}

    total_edep = sum(edep_by_region.values())
    dose_rows = []
    for i,r in regions.items():
        edep_keV = edep_by_region.get(i,0.0)
        mat = materials.get(i, {})
        dose_rows.append({
            'region_id': i,
            'region_key': r['region_key'],
            'description': r.get('description',''),
            'material_name': mat.get('material_name',''),
            'material_class': mat.get('material_class',''),
            'density_g_cm3': mat.get('density_g_cm3',''),
            'events': n_events,
            'edep_keV': edep_keV,
            'edep_per_event_keV': edep_keV/max(n_events,1),
            'edep_J': edep_keV*KEV_TO_J,
            'scoring_mass_kg': masses.get(i, ''),
            'simulated_absorbed_dose_Gy': (edep_keV*KEV_TO_J/masses[i]) if masses.get(i, 0)>0 else '',
            'absorbed_dose_per_incident_history_Gy': (edep_keV*KEV_TO_J/(masses[i]*max(n_events,1))) if masses.get(i, 0)>0 else '',
            # Absolute Gy should be taken from the Geant4 region mass printout or a validated geometry-volume table.
            # This CSV now includes the material/density map used in Stage 1 for traceability.
            'relative_fraction_of_scored_edep': edep_keV/total_edep if total_edep>0 else 0.0,
        })
    with open(outdir/'compartment_dose.csv','w',newline='') as fcsv:
        w=csv.DictWriter(fcsv, fieldnames=list(dose_rows[0].keys()))
        w.writeheader(); w.writerows(dose_rows)

    # Full edep hit table, kept compact enough for plotting.
    if steps and not args.skip_step_csv:
        with open(outdir/'edep_hits.csv','w',newline='') as fcsv:
            fields=['eventID','regionID','region_key','pdg','trackID','parentID','edep_keV','ekin_pre_keV','step_um','x_um','y_um','z_um']
            w=csv.DictWriter(fcsv, fieldnames=fields); w.writeheader()
            for row in steps:
                rid=int(row.regionID); rkey=regions.get(rid,{}).get('region_key','unknown')
                w.writerow({k:getattr(row,k) for k in ['eventID','regionID','pdg','trackID','parentID','edep_keV','ekin_pre_keV','step_um','x_um','y_um','z_um']} | {'region_key':rkey})

    # Preserve every secondary in secondaries.csv, but use only valid electron
    # creation points for the biologically interpreted table and chemistry spectra.
    spectra = {i:[] for i in regions}
    n_all_secondaries = 0
    n_electrons = 0
    n_electrons_excluded_outside_body = 0
    if secondaries:
        base_fields=['eventID','regionID','region_key','parentPDG','secondaryPDG','ekin_keV','x_um','y_um','z_um']
        optional_fields=['insideBody','parentStep_um','parentPreX_um','parentPreY_um','parentPreZ_um','parentPostX_um','parentPostY_um','parentPostZ_um']
        available_optional=[name for name in optional_fields if secondaries.GetBranch(name)]
        fields=base_fields+available_optional
        with open(outdir/'secondaries.csv','w',newline='') as fall, open(outdir/'secondary_electrons.csv','w',newline='') as fe:
            wall=csv.DictWriter(fall, fieldnames=fields); wall.writeheader()
            we=csv.DictWriter(fe, fieldnames=fields); we.writeheader()
            for row in secondaries:
                rid=int(row.regionID); spdg=int(row.secondaryPDG); e=float(row.ekin_keV)
                rkey=regions.get(rid,{}).get('region_key','unknown')
                rec={k:getattr(row,k) for k in ['eventID','regionID','parentPDG','secondaryPDG','ekin_keV','x_um','y_um','z_um']}
                rec.update({name:getattr(row,name) for name in available_optional})
                rec['region_key']=rkey
                wall.writerow(rec)
                n_all_secondaries += 1
                if spdg != 11:
                    continue
                n_electrons += 1
                inside_body = int(rec.get('insideBody', 1)) == 1
                if not inside_body:
                    n_electrons_excluded_outside_body += 1
                    continue
                we.writerow(rec)
                if e > 0:
                    spectra.setdefault(rid,[]).append(e)
    # log-spaced bins; chemistry reader accepts energy_keV,weight rows.
    edges=[args.emin_kev*((args.emax_kev/args.emin_kev)**(j/args.bins)) for j in range(args.bins+1)]
    for rid, vals in spectra.items():
        name=regions.get(rid,{}).get('region_key',f'region{rid}')
        counts=[0]*args.bins
        for e in vals:
            if e < edges[0] or e > edges[-1]:
                continue
            j=min(args.bins-1, max(0, int(math.log(e/edges[0])/math.log(edges[-1]/edges[0])*args.bins)))
            counts[j]+=1
        out=outdir/f'electron_spectrum_region{rid}_{name}.csv'
        with open(out,'w',newline='') as fcsv:
            w=csv.writer(fcsv); w.writerow(['energy_keV','weight'])
            for j,c in enumerate(counts):
                if c>0:
                    center=(edges[j]*edges[j+1])**0.5
                    w.writerow([f'{center:.8g}', c])
    summary={
        'root_file': os.path.abspath(args.root_file),
        'events': n_events,
        'total_scored_edep_keV': total_edep,
        'target_dose_rate_Gy_s': args.target_dose_rate,
        'pulse_s': args.pulse_s,
        'expected_total_dose_Gy': args.target_dose_rate*args.pulse_s,
        'materials_csv': str(Path(args.materials).resolve()) if args.materials else None,
        'transport_log': str(Path(args.transport_log).resolve()) if args.transport_log else None,
        'n_all_secondaries': n_all_secondaries,
        'n_valid_electron_secondaries': n_electrons - n_electrons_excluded_outside_body,
        'n_electron_secondaries_excluded_outside_body': n_electrons_excluded_outside_body,
        'regions': dose_rows,
    }
    with open(outdir/'transport_summary.json','w') as fjson:
        json.dump(summary,fjson,indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
