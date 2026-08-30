#!/usr/bin/env python3
"""Build and execute one provenance-complete transport + nervous scoring case."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()

def run(command, cwd, log=None):
    print("+", " ".join(map(str, command)), flush=True)
    if log:
        with log.open("w") as handle: subprocess.run(command,cwd=cwd,stdout=handle,stderr=subprocess.STDOUT,check=True)
    else: subprocess.run(command,cwd=cwd,check=True)

def find_analysis_python(explicit=None):
    """Find a Python containing the VTK/pandas/trimesh scoring dependencies."""
    candidates=[explicit,os.environ.get("ROSWORM_ANALYSIS_PYTHON"),sys.executable,
                str(Path.home()/"miniconda3/envs/ros/bin/python"),
                str(Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
                shutil.which("python3")]
    checked=[]
    for candidate in candidates:
        if not candidate or candidate in checked: continue
        checked.append(candidate)
        probe=subprocess.run([candidate,"-c","import numpy,pandas,trimesh,vtk"],
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if probe.returncode==0: return candidate
    raise SystemExit("No analysis Python has numpy, pandas, trimesh, and VTK. "
                     "Pass --analysis-python or set ROSWORM_ANALYSIS_PYTHON.")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--case", choices=["focused_avoidance_50kv","focused_egg_ejection_50kv","diffuse_paralysis_20kv"], required=True)
    parser.add_argument("--events", type=int, default=100000)
    parser.add_argument("--threads", type=int, default=min(16,os.cpu_count() or 1))
    parser.add_argument("--seed-a", type=int, default=1357911); parser.add_argument("--seed-b", type=int, default=2468022)
    parser.add_argument("--run-name", default=None); parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-nervous-scoring", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume post-processing when transport outputs already exist")
    parser.add_argument("--analysis-python", default=None,
                        help="Python with numpy/pandas/trimesh/VTK for geometry scoring")
    args=parser.parse_args()

    stage=Path(__file__).resolve().parents[1]; repo=stage.parent
    config=yaml.safe_load((stage/"config/bolding_cases.yaml").read_text()); case=config["cases"][args.case]
    run_name=args.run_name or f"{args.case}_{args.events}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    result=stage/"results"/run_name
    if result.exists() and not args.resume: raise SystemExit(f"Refusing to overwrite existing result directory: {result}")
    result.mkdir(parents=True,exist_ok=True)
    build=stage/"transport_manifest/build"; binary=build/"ros_worm_manifest"
    if not args.skip_build:
        run(["cmake","-S",str(stage/"transport_manifest"),"-B",str(build),"-DCMAKE_BUILD_TYPE=Release"],repo)
        run(["cmake","--build",str(build),"-j",str(args.threads)],repo)

    macro=[f"/run/numberOfThreads {args.threads}",f"/random/setSeeds {args.seed_a} {args.seed_b}",
           f"/rosworm/materials {stage/'config/region_materials.csv'}",f"/rosworm/manifest {stage/'config/transport_geometry_v1.csv'}",
           "/rosworm/mmPerUnit 0.1","/rosworm/maxStep_um 2 um","/rosworm/saveSteps true",
           f"/rosworm/sourceType {case['source_type']}",f"/rosworm/spectrumType {case['spectrum_type']}",
           f"/rosworm/kvp {case['kvp_keV']} keV",f"/rosworm/minEnergy {case['min_energy_keV']} keV",
           f"/rosworm/sourceY {case['source_y_mm']} mm"]
    if case["source_type"]=="focused": macro.append(f"/rosworm/spotFWHM {case['spot_fwhm_mm']} mm")
    else: macro += [f"/rosworm/halfX {case['half_x_mm']} mm",f"/rosworm/halfZ {case['half_z_mm']} mm"]
    macro += ["/run/initialize","/tracking/verbose 0",f"/run/printProgress {max(1,args.events//10)}",f"/run/beamOn {args.events}"]
    macro_path=result/"transport.mac"; log=result/"transport.log"
    if not args.resume or not (result/"output0.root").exists():
        macro_path.write_text("\n".join(macro)+"\n")
        run([str(binary),str(macro_path)],result,log)

    reference_rate=max(case["dose_rates_Gy_s"])
    if not args.resume or not (result/"transport_summary.json").exists():
        run(["python3",str(stage/"scripts/extract_transport_outputs.py"),str(result/"output0.root"),"--regions",str(stage/"config/regions.csv"),
             "--materials",str(stage/"config/region_materials.csv"),"--transport-log",str(log),"--outdir",str(result),
             "--target-dose-rate",str(reference_rate),"--pulse-s",str(case["pulse_s"]),"--skip-step-csv"],repo)
    run(["python3",str(stage/"scripts/summarize_navigation_warnings.py"),str(log),"--outdir",str(result)],repo)
    scoring_metadata=result/"nervous_surface_scoring/nervous_surface_scoring_metadata.json"
    if not args.skip_nervous_scoring and (not args.resume or not scoring_metadata.exists()):
        analysis_python=find_analysis_python(args.analysis_python)
        run([analysis_python,str(stage/"scripts/score_nervous_surface_v1.py"),"--secondaries",str(result/"secondaries.csv"),
             "--nervous-stl",str(repo/"openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"),
             "--placement-manifest",str(stage/"config/transport_geometry_v1.csv"),"--outdir",str(result/"nervous_surface_scoring")],repo)

    git_sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
    git_status=subprocess.check_output(["git","status","--short"],cwd=repo,text=True).splitlines()
    artifacts={}
    for path in [macro_path,stage/"config/transport_geometry_v1.csv",stage/"config/region_materials.csv",repo/"openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"]:
        key=str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)
        artifacts[key]={"sha256":sha256(path),"bytes":path.stat().st_size}
    manifest={"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),"git_commit":git_sha,"git_status_at_run":git_status,
              "case_name":args.case,"case":case,"events":args.events,"threads":args.threads,"random_seeds":[args.seed_a,args.seed_b],
              "geant4_version":subprocess.check_output(["geant4-config","--version"],text=True).strip(),"artifacts":artifacts,
              "result_directory":str(result.resolve())}
    (result/"run_manifest.json").write_text(json.dumps(manifest,indent=2)); print(f"[OK] {result}")

if __name__ == "__main__": main()
