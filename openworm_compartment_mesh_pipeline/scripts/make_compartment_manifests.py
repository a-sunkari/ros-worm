#!/usr/bin/env python3
"""Classify repaired OpenWorm per-object STL manifest into mesh-compartment roles.

This script intentionally produces manifests for a *mesh compartment* workflow, not a voxel phantom.
"""
import argparse, json, re
from pathlib import Path
import pandas as pd

PHARYNX_PREFIXES = ("pm", "mc")
PHARYNX_EXACT_PREFIXES = ("Phar_Gland", "Arcade_Cell")
REPRO_PREFIXES = ("Sp_", "Gonadal", "Rachis", "Oocyte", "ut", "uv", "vul", "vm", "um", "vpi")
SUPPORT_PATTERNS = [r"sh", r"so", r"GLR"]

# conservative list of known broad prefixes/names. Anything uncertain becomes scoring/review, not material.
def infer_role(name: str) -> tuple[str, str, str]:
    n = name.strip()
    nl = n.lower()

    # outer body / envelope
    if n == "Cuticle":
        return "whole_body", "physical_parent", "outer body contour / parent volume"

    # hypodermis / seam. Treat as material candidate only after shell logic is decided.
    if re.fullmatch(r"hyp\d+", n) or n.startswith("Seam_Cells"):
        return "hypodermis_shell", "defer_physical", "hypodermis/seam shell or scoring label; not first-pass child"

    # intestine
    if nl.startswith("int"):
        return "digestive_system", "physical_child_candidate", "intestine"

    # pharyngeal muscles/cells/glands/arcade. Exclude I1/I2/etc as those are likely pharyngeal neurons/scoring.
    if n.startswith(PHARYNX_PREFIXES) or any(n.startswith(p) for p in PHARYNX_EXACT_PREFIXES) or re.fullmatch(r"e[123].*", n):
        return "digestive_system", "physical_child_candidate", "pharynx/mouth/digestive"

    # reproductive / rectal-ish system. Keep rect/anus in this broad internal-compartment bucket for testing.
    if n.startswith(REPRO_PREFIXES) or nl.startswith("rect") or n == "Anus" or nl.startswith("mu_anal"):
        return "reproductive_rectal_system", "physical_child_candidate", "reproductive/rectal aggregate candidate"

    # body wall muscle
    if n.startswith("mu_bod"):
        return "bodywall_muscle", "physical_child_candidate", "body-wall muscle aggregate candidate"

    # excretory
    if n.startswith("Excretory"):
        return "excretory_system", "physical_child_candidate", "excretory cell/system candidate"

    # explicit problematic neurons from current repair; keep scoring first
    if n in {"PVDL", "PVDR"}:
        return "nervous_system", "scoring_only_problem_mesh", "PVD neuron; still defective in Geant4 after repair"

    # support/sheath/socket by name fragments/suffixes, plus GLR support cells
    if any(re.search(p, n, re.IGNORECASE) for p in SUPPORT_PATTERNS):
        return "support_sheath_socket", "scoring_only", "support/sheath/socket/glial-like scoring atlas"

    # many neuron names are all-caps with L/R/D/V suffixes; avoid making them physical by default.
    # C. elegans cell/neuron names often are 2-5 uppercase letters plus optional L/R/D/V digits.
    if re.fullmatch(r"[A-Z]{1,5}[A-Z0-9]*[LRDV]?\d*", n) or re.fullmatch(r"[A-Z]{2,5}[LRDV]\d*", n):
        return "nervous_system", "scoring_only", "neuron/cell scoring atlas"

    # Pharyngeal neurons I1-I6 or M cells should be scoring first, not material.
    if re.fullmatch(r"I\d.*", n) or re.fullmatch(r"M\d.*", n):
        return "nervous_or_pharyngeal_scoring", "scoring_only", "pharyngeal neuron/cell scoring atlas"

    # cube / scale / misc
    if n.lower().startswith("cube") or n in {"1um","10um","100um","1mm"}:
        return "exclude", "exclude", "scale/helper object"

    return "review", "manual_review", "unclassified; inspect before physical use"

def write_manifest(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[write] {path} rows={len(df)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.manifest)
    if "object_name" not in df.columns or "stl_path" not in df.columns:
        raise SystemExit("manifest must contain object_name and stl_path")

    roles = df["object_name"].astype(str).apply(infer_role)
    df["compartment"] = [r[0] for r in roles]
    df["geometry_role"] = [r[1] for r in roles]
    df["role_note"] = [r[2] for r in roles]

    # Keep original category_guess if present; validator requires it. Add if absent.
    if "category_guess" not in df.columns:
        df["category_guess"] = df["compartment"]
    # Existing validator filters category_guess, so also provide a validator_category column for clarity.
    df["validator_category"] = df["compartment"]

    write_manifest(df, outdir / "manifest_with_compartment_roles.csv")

    material_children = df[df["geometry_role"].eq("physical_child_candidate")].copy()
    wu_core = material_children[material_children["compartment"].isin(["digestive_system", "reproductive_rectal_system"])].copy()
    wu_core_no_rectal = material_children[material_children["compartment"].isin(["digestive_system"])].copy()
    scoring = df[df["geometry_role"].str.startswith("scoring", na=False)].copy()
    deferred = df[df["geometry_role"].eq("defer_physical")].copy()
    parent = df[df["geometry_role"].eq("physical_parent")].copy()
    review = df[df["geometry_role"].isin(["manual_review", "exclude"])].copy()

    # For validator compatibility, category_guess should reflect compartment in these generated manifests.
    for d in [material_children, wu_core, wu_core_no_rectal, scoring, deferred, parent, review]:
        d["category_guess"] = d["compartment"]

    write_manifest(parent, outdir / "manifest_whole_body_parent.csv")
    write_manifest(wu_core, outdir / "manifest_wu_core_children.csv")
    write_manifest(material_children, outdir / "manifest_material_children_no_body.csv")
    write_manifest(scoring, outdir / "manifest_scoring_atlas.csv")
    write_manifest(deferred, outdir / "manifest_deferred_shells.csv")
    write_manifest(review, outdir / "manifest_review_or_exclude.csv")

    groups = {}
    for comp, sub in df[df["geometry_role"].ne("exclude")].groupby("compartment"):
        groups[comp] = sub["object_name"].astype(str).tolist()
    # Common aliases
    groups["whole_body"] = parent["object_name"].astype(str).tolist()
    groups["wu_core_children"] = wu_core["object_name"].astype(str).tolist()
    groups["material_children_no_body"] = material_children["object_name"].astype(str).tolist()
    (outdir / "compartment_groups.json").write_text(json.dumps(groups, indent=2))

    summary = df.groupby(["compartment", "geometry_role"]).size().reset_index(name="count").sort_values(["geometry_role","compartment"])
    write_manifest(summary, outdir / "role_summary.csv")
    print("\nRole summary:")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
