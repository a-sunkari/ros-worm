#!/usr/bin/env python3
"""Generate the nine paper-facing ROS-Worm final figures as PNG and PDF."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np
import pandas as pd

C={"focused":"#1769aa","diffuse":"#d95f02","neural":"#4c78a8","muscle":"#e45756","model":"#4c78a8","chemical":"#e3a322","observed":"#3a7d44","unsupported":"#b7b7b7"}

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def save(fig,out,stem,title,records):
    fig.suptitle(title,x=.02,ha="left",fontsize=12,fontweight="bold"); fig.tight_layout(rect=(0,0,1,.95))
    for ext in ("png","pdf"): fig.savefig(out/f"{stem}.{ext}",dpi=350 if ext=="png" else None,bbox_inches="tight")
    plt.close(fig); records.append({"figure":stem,"title":title,"png_sha256":sha(out/f"{stem}.png"),"pdf_sha256":sha(out/f"{stem}.pdf")})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,required=True); ap.add_argument("--outdir",type=Path,required=True)
    a=ap.parse_args(); repo=a.repo.resolve(); out=a.outdir.resolve(); out.mkdir(parents=True,exist_ok=True)
    vf=repo/"ros_worm_stage1/validation/final"; v21=repo/"ros_worm_stage1/validation/v2_1"; tables=vf/"tables"
    mpl.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.titlesize":9.5,"axes.labelsize":9,"legend.fontsize":7.3,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"white"})
    rec=[]

    # 1: experiment-to-analysis workflow and evidentiary boundary.
    fig,ax=plt.subplots(figsize=(9.2,3)); ax.axis("off")
    nodes=[("50 kV W focused\n+ NGM / dish","observed"),("20 kV Ag diffuse\n+ M9 / glass","observed"),("Geant4 transport\nstable compartments","model"),("actual edep steps\n0.5 µm charged limit","model"),("neural union ROI +\noriginal surface","model"),("water radiolysis +\nTrp/redox opportunity","chemical"),("LITE-1 gating /\nbehavior","unsupported")]
    xs=np.linspace(.07,.93,len(nodes)); y=.55
    for i,((lab,status),x) in enumerate(zip(nodes,xs)):
        box=FancyBboxPatch((x-.06,y-.16),.12,.32,boxstyle="round,pad=.01",transform=ax.transAxes,facecolor=C[status],edgecolor="none")
        ax.add_patch(box); ax.text(x,y,lab,ha="center",va="center",transform=ax.transAxes,color="white" if status!="unsupported" else "#333",fontweight="bold",fontsize=7)
        if i<len(nodes)-1: ax.annotate("",xy=(xs[i+1]-.065,y),xytext=(x+.065,y),xycoords=ax.transAxes,arrowprops={"arrowstyle":"->","lw":1.4,"ls":"--" if i>=4 else "-","color":C["chemical"] if i>=4 else C["model"]})
    ax.legend(handles=[Patch(color=C["observed"],label="experiment-defined"),Patch(color=C["model"],label="model-supported"),Patch(color=C["chemical"],label="chemical opportunity"),Patch(color=C["unsupported"],label="not quantitatively modeled")],loc="lower center",ncol=4,frameon=False)
    save(fig,out,"fig01_geometry_workflow","Experimental configurations, computation, and mechanistic boundary",rec)

    # 2: ROI convergence and localized outlier audit.
    conv=pd.read_csv(v21/"neural_roi/neural_roi_resolution_convergence.csv"); ol=pd.read_csv(vf/"neural_roi/surface_outlier_localization.csv")
    fig,axs=plt.subplots(1,3,figsize=(9,3.1)); axs[0].plot(conv.pitch_um,conv.volume_um3,"o-",color=C["neural"]); axs[0].set(xscale="log",xlabel="voxel pitch (µm)",ylabel="neural volume (µm³)"); axs[0].set_xticks(conv.pitch_um,[f"{x:g}" for x in conv.pitch_um]); axs[0].grid(alpha=.2)
    for col,lab in [("surface_error_p50_um","p50"),("surface_error_p95_um","p95"),("surface_error_p99_um","p99")]: axs[1].plot(conv.pitch_um,conv[col],"o-",label=lab)
    axs[1].set(xscale="log",yscale="log",xlabel="voxel pitch (µm)",ylabel="symmetric surface error (µm)"); axs[1].set_xticks(conv.pitch_um,[f"{x:g}" for x in conv.pitch_um]); axs[1].legend(); axs[1].grid(alpha=.2)
    o=ol[ol.direction=="reference_to_roi"]; axs[2].bar(o.threshold_um,100*o.outlier_fraction,width=[.5,2,4,8],color=C["neural"]); axs[2].set(xlabel="distance threshold (µm)",ylabel="reference samples beyond threshold (%)",yscale="log"); axs[2].grid(axis="y",alpha=.2)
    save(fig,out,"fig02_neural_roi_validation","Analysis-only neural ROI convergence and localized surface outliers",rec)

    # 3: regional dose with MC uncertainty and reconstruction range.
    st=pd.read_csv(vf/"statistics/final_nominal_dose_statistics.csv"); dose=pd.read_csv(vf/"production/production_neural_muscle_dose.csv")
    fig,ax=plt.subplots(figsize=(6.8,3.6)); x=np.arange(2); w=.34
    for j,(region,prefix) in enumerate([("neural","neural_"),("muscle","physical_")]):
        rows=[]
        for irr in ("focused","diffuse"):
            r=st[(st.irradiation==irr)&st.roi.str.startswith(prefix)].iloc[0]; rows.append(r)
        ax.bar(x+(j-.5)*w,[r.roi_to_whole_dose_ratio for r in rows],w,yerr=[1.96*r.delta_method_se for r in rows],capsize=3,color=C[region],label=f"{region.capitalize()} (95% MC CI)")
    for i,irr in enumerate(("focused","diffuse")):
        v=dose[(dose.irradiation==irr)&dose.roi.str.startswith("neural_voxel_")].dose_ratio_roi_to_whole_worm
        ax.plot([x[i]-w*.5]*2,[v.min(),v.max()],color="#222",lw=5,solid_capstyle="round",label="ROI-pitch range" if i==0 else None)
    ax.axhline(1,color="#555",ls="--"); ax.set(xticks=x,xticklabels=["Focused + NGM","Diffuse + M9"],ylabel="regional dose / whole-worm mean dose"); ax.legend(); ax.grid(axis="y",alpha=.2)
    save(fig,out,"fig03_regional_dose","Neural and body-wall-muscle dose from 100-million-history transport",rec)

    # 4: shell-resolved neural/muscle edep and matched null.
    surf=pd.read_csv(tables/"neural_muscle_surface_edep_shells.csv"); fig,axs=plt.subplots(1,2,figsize=(9,3.5))
    labels=surf[(surf.irradiation=="focused")&(surf.surface=="nervous")].shell_label.tolist(); xx=np.arange(len(labels))
    for irr,ls in [("focused","-"),("diffuse","--")]:
        for s,col in [("nervous",C["neural"]),("muscle",C["muscle"])]:
            q=surf[(surf.irradiation==irr)&(surf.surface==s)]; axs[0].plot(xx,100*q.whole_worm_edep_fraction,"o",ls=ls,color=col,label=f"{irr}, {s}")
    axs[0].set(xticks=xx,xticklabels=labels,xlabel="surface-distance shell (µm)",ylabel="whole-worm edep (%)"); axs[0].tick_params(axis="x",rotation=25); axs[0].legend(ncol=2); axs[0].grid(alpha=.2)
    for i,irr in enumerate(("focused","diffuse")):
        n=pd.read_csv(vf/f"nulls/{irr}/nervous_surface_edep_matched_nulls.csv"); meta=json.loads((vf/f"nulls/{irr}/edep_control_metadata.json").read_text()); y=n.edep_fraction_within_5um
        axs[1].boxplot(y,positions=[i],widths=.5,showfliers=False); axs[1].scatter([i], [meta["real"]["edep_fraction_within_5um"]],marker="*",s=80,color=C[irr],zorder=4,label=f"real {irr}, p={meta['null_empirical_upper_tail_p_within_5um']:.2f}")
    axs[1].set(xticks=[0,1],xticklabels=["Focused","Diffuse"],ylabel="0–5 µm edep fraction",title="99 matched-atlas nulls (1M prefix)"); axs[1].legend(); axs[1].grid(axis="y",alpha=.2)
    save(fig,out,"fig04_surface_edep_nulls","Actual deposited energy near nervous and muscle surfaces",rec)

    # 5: longitudinal spatial deposition.
    prof=pd.read_csv(tables/"longitudinal_edep_profiles.csv"); fig,axs=plt.subplots(1,2,figsize=(8.5,3.4),sharey=True)
    for ax,irr in zip(axs,("focused","diffuse")):
        q=prof[prof.irradiation==irr]
        for reg,col,ls in [("whole_worm","#333","-"),("within_5um_nervous_surface",C["neural"],"-"),("within_5um_muscle_surface",C["muscle"],"--")]:
            z=q[q.region==reg]; ax.plot(z.y_center_um,100*z.whole_worm_edep_fraction,color=col,ls=ls,label=reg.replace("_"," "))
        ax.set(xlabel="longitudinal Y (µm)",title=irr.capitalize()); ax.grid(alpha=.2)
    axs[0].set_ylabel("whole-worm edep per 20 µm bin (%)"); axs[0].legend(fontsize=6.5)
    save(fig,out,"fig05_longitudinal_edep","Focused and diffuse longitudinal deposited-energy distributions",rec)

    # 6: exposure-to-regional-dose mapping.
    cannon=pd.read_csv(tables/"final_cannon_condition_table.csv"); fig,axs=plt.subplots(1,2,figsize=(8,3.5),sharey=True)
    for ax,irr in zip(axs,("focused","diffuse")):
        q=cannon[cannon.source_type==irr].sort_values("reported_whole_worm_dose_Gy")
        ax.plot(q.reported_whole_worm_dose_Gy,q.neural_Gy,"o-",color=C["neural"],label="neural")
        ax.plot(q.reported_whole_worm_dose_Gy,q.muscle_Gy,"o-",color=C["muscle"],label="muscle")
        ax.plot(q.reported_whole_worm_dose_Gy,q.reported_whole_worm_dose_Gy,"--",color="#555",label="whole mean")
        ax.set(xlabel="reported whole-worm dose (Gy)",title=irr.capitalize()); ax.grid(alpha=.2)
    axs[0].set_ylabel("modeled regional dose (Gy)"); axs[0].legend()
    save(fig,out,"fig06_cannon_dose_mapping","Cannon conditions translated to neural and muscle dose",rec)

    # 7: all implemented major radiolysis species per local joule.
    chem=pd.read_csv(vf/"chemistry/edep_weighted_chemistry_timeseries.csv"); species=["°OH^0","H2O2^0","e_aq^-1","H^0","H3O^1"]
    fig,axs=plt.subplots(1,2,figsize=(8.5,3.6),sharey=True)
    for ax,irr in zip(axs,("focused","diffuse")):
        for sp in species:
            q=chem[(chem.irradiation==irr)&(chem.analysis_region=="neural")&(chem.species==sp)].sort_values("time_ns")
            ax.plot(q.time_ns,q.mean_G_molecules_per_100eV,"o-",ms=2,label=sp)
        ax.set(xscale="log",yscale="log",xlabel="spur time (ns)",title=f"{irr.capitalize()} neural edep-weighted spectrum"); ax.grid(alpha=.2,which="both")
    axs[0].set_ylabel("G value (molecules / 100 eV)"); axs[0].legend(ncol=2)
    save(fig,out,"fig07_radiolysis_timecourse","Time-resolved homogeneous-water radiolysis from local deposited energy",rec)

    # 8: target opportunity range by exposure.
    fig,ax=plt.subplots(figsize=(7.4,4)); q=cannon.copy(); x=np.arange(len(q));
    for j,(low,high,col,label) in enumerate([("Trp_interaction_opportunity_low","Trp_interaction_opportunity_high",C["neural"],"Trp-like"),("thiol_interaction_opportunity_low","thiol_interaction_opportunity_high",C["chemical"],"thiol-like")]):
        xx=x+(j-.5)*.22; ax.vlines(xx,q[low],q[high],color=col,lw=5,alpha=.75,label=label); ax.scatter(xx,np.sqrt(q[low]*q[high]),color=col,s=12)
    short=[f"{'F' if r.source_type=='focused' else 'D'} {r.reported_dose_rate_Gy_s:g}×{r.exposure_s:g}s" for _,r in q.iterrows()]
    ax.set(yscale="log",xticks=x,xticklabels=short,ylabel="neural interaction opportunity (range)"); ax.tick_params(axis="x",rotation=25,labelsize=7); ax.legend(); ax.grid(axis="y",alpha=.2,which="both")
    save(fig,out,"fig08_target_opportunities","LITE-1-relevant Level-1 chemical interaction opportunities",rec)

    # 9: separated uncertainty budget.
    ub=pd.read_csv(tables/"final_uncertainty_budget.csv"); ub=ub[(ub.endpoint=="neural/whole-worm dose ratio")&~ub.uncertainty_source.str.contains("dosimetry")]
    fig,axs=plt.subplots(1,2,figsize=(8.5,3.8),sharex=True)
    for ax,irr in zip(axs,("focused","diffuse")):
        q=ub[ub.irradiation==irr].reset_index(drop=True); c=q.central.iloc[0]
        for i,r in q.iterrows(): ax.plot([100*(r.lower/c-1),100*(r.upper/c-1)],[i,i],lw=6,solid_capstyle="round",color=C[irr])
        ax.axvline(0,color="#333",lw=.8); ax.set(yticks=range(len(q)),yticklabels=q.uncertainty_source,xlabel="relative interval (%)",title=irr.capitalize()); ax.grid(axis="x",alpha=.2)
    save(fig,out,"fig09_uncertainty_budget","Neural-dose uncertainty sources kept separate",rec)

    sources=list(tables.glob("*.csv"))+list((vf/"statistics").glob("*.csv"))+list((vf/"chemistry").glob("*.csv"))
    (out/"figure_manifest.json").write_text(json.dumps({"schema_version":1,"figures":rec,"source_hashes":{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+"\n")

if __name__=="__main__": main()
