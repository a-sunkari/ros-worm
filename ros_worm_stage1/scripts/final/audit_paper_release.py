#!/usr/bin/env python3
"""Fail-loud deterministic audit for the paper-ready ROS-Worm release."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import pandas as pd

EXPECTED_ROOT={"focused":"9ca894f34111914a9722922185ab4c63c0f21b3aba7e37e46e9d202b32188e91","diffuse":"6f0dccd1e504f44e6ea7889c17bfaf0b23e4aaa01df229a5548d68d3ba0f6d4d"}
EXPECTED_ROI="69bf318ee42796258993035ed87c2954f05b21ff1887bbb1a9ef2497afc84475"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); r=a.repo.resolve(); vf=r/"ros_worm_stage1/validation/final"; checks=[]
    def check(name,ok,evidence):
        checks.append({"check":name,"passed":bool(ok),"evidence":str(evidence)})
        if not ok: raise SystemExit(f"RELEASE AUDIT FAILED: {name}: {evidence}")

    branch=subprocess.check_output(["git","branch","--show-current"],cwd=r,text=True).strip(); check("branch",branch=="ai/paper-ready-final",branch)
    idx=pd.read_csv(vf/"production/production_run_index.csv")
    for irr in ("focused","diffuse"):
        q=idx[idx.irradiation==irr].iloc[0]; check(f"{irr} histories",int(q.events)==100_000_000,q.events); check(f"{irr} ROOT hash",q.root_sha256==EXPECTED_ROOT[irr],q.root_sha256)
        md=json.loads((vf/f"production/{irr}/edep_scoring_metadata.json").read_text()); check(f"{irr} energy conservation",md["step_minus_event_edep_keV"]==0,md["step_minus_event_edep_keV"])
        check(f"{irr} active step limit",float(q.charged_max_step_um)==.5,q.charged_max_step_um)
    conv=pd.read_csv(r/"ros_worm_stage1/validation/v2_1/neural_roi/neural_roi_resolution_convergence.csv")
    check("four ROI pitches",set(conv.pitch_um)=={.25,.5,1,2},list(conv.pitch_um)); check("primary ROI hash",conv.loc[conv.pitch_um==.25,"roi_sha256"].iloc[0]==EXPECTED_ROI,conv.loc[conv.pitch_um==.25,"roi_sha256"].iloc[0])
    roi=json.loads((vf/"neural_roi/neural_roi_final_audit.json").read_text()); check("276 valid neural members",roi["source_members"]==276 and roi["all_watertight_after_vertex_merge"] and roi["all_winding_consistent"] and roi["all_positive_signed_interiors"],roi)
    st=pd.read_csv(vf/"statistics/final_nominal_dose_statistics.csv"); check("four final dose estimators",len(st)==4,len(st)); check("neural RSE <=10%",((st[st.roi.str.startswith("neural_")].delta_method_se/st[st.roi.str.startswith("neural_")].roi_to_whole_dose_ratio)<=.10).all(),st[st.roi.str.startswith("neural_")][["irradiation","delta_method_se","roi_to_whole_dose_ratio"]].to_dict("records"))
    check("bootstrap count",(st.bootstrap_replicates==2000).all(),list(st.bootstrap_replicates))
    for irr in ("focused","diffuse"):
        n=pd.read_csv(vf/f"nulls/{irr}/nervous_surface_edep_matched_nulls.csv"); check(f"{irr} 99 matched nulls",len(n)==99,len(n))
    ci=pd.read_csv(vf/"chemistry/chemistry_run_index.csv"); check("six chemistry cases",len(ci)==6,len(ci)); check("chemistry 10k each",(ci.events==10000).all(),list(ci.events))
    ts=pd.read_csv(vf/"chemistry/edep_weighted_chemistry_timeseries.csv"); check("seven chemistry times",ts.time_ns.nunique()==7,sorted(ts.time_ns.unique())); check("implemented key species",set(["°OH^0","H2O2^0","e_aq^-1","H^0","H3O^1"]).issubset(set(ts.species)),sorted(ts.species.unique()))
    required=["final_nominal_regional_dose.csv","final_uncertainty_budget.csv","final_cannon_condition_table.csv","neural_muscle_surface_edep_shells.csv","longitudinal_edep_profiles.csv","transport_qc_and_navigation.csv"]
    for f in required: check(f"table {f}",(vf/"tables"/f).is_file(),vf/"tables"/f)
    figm=json.loads((vf/"figures/figure_manifest.json").read_text()); check("nine final figures",len(figm["figures"])==9,len(figm["figures"]))
    for f in figm["figures"]:
        for ext in ("png","pdf"): check(f"{f['figure']} {ext} hash",sha(vf/"figures"/f"{f['figure']}.{ext}")==f[f"{ext}_sha256"],f["figure"])
    reqman=["ROS_WORM_MANUSCRIPT.md","TITLE_ABSTRACT.md","INTRODUCTION.md","METHODS.md","RESULTS.md","DISCUSSION.md","FIGURE_CAPTIONS.md","REFERENCES.md","SUPPLEMENTARY_METHODS.md","SUPPLEMENTARY_TABLES.md"]
    for f in reqman: check(f"manuscript {f}",(r/"manuscript"/f).is_file(),f)
    text=(r/"manuscript/ROS_WORM_MANUSCRIPT.md").read_text();
    for stale in ("0.778 ± 0.101","0.969 ± 0.224","only 30 contributing events"):
        check(f"stale manuscript token absent: {stale}",stale not in text,stale)
    required_docs=["docs/final/JOURNAL_POSITIONING.md","docs/final/LITE1_EVIDENCE_AUDIT.md","docs/final/REVIEWER_2_REPORT.md","docs/final/RESPONSE_TO_REVIEWER_2.md","FINAL_PROJECT_STATUS.md"]
    for f in required_docs: check(f"release document {f}",(r/f).is_file(),f)
    payload={"schema_version":1,"status":"PASS","branch":branch,"checks":checks,"authoritative_hashes":{"focused_root":EXPECTED_ROOT["focused"],"diffuse_root":EXPECTED_ROOT["diffuse"],"neural_roi_0.25um":EXPECTED_ROI}}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(payload,indent=2)+"\n"); print(f"PASS: {len(checks)} release checks")

if __name__=="__main__": main()
