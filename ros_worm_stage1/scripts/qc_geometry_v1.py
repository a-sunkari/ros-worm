#!/usr/bin/env python3
"""Quantitative QC for physical geometry and candidate nervous representations."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
import matplotlib.pyplot as plt

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def mesh_row(name,path):
    m=trimesh.load_mesh(path,force='mesh',process=True)
    counts=np.bincount(m.edges_unique_inverse)
    return m,{"name":name,"path":str(Path(path).resolve()),"sha256":sha(path),"faces":len(m.faces),"vertices":len(m.vertices),
      "face_connected_components":len(m.split(only_watertight=False)),"vertex_connected_components":m.body_count,
      "watertight":bool(m.is_watertight),"winding_consistent":bool(m.is_winding_consistent),
      "boundary_edges":int((counts==1).sum()),"nonmanifold_edges":int((counts>2).sum()),"volume_model_units3":float(m.volume),
      "min_x":m.bounds[0,0],"min_y":m.bounds[0,1],"min_z":m.bounds[0,2],"max_x":m.bounds[1,0],"max_y":m.bounds[1,1],"max_z":m.bounds[1,2]}

def vtk_poly(mesh):
    points=vtk.vtkPoints(); points.SetData(numpy_to_vtk(np.asarray(mesh.vertices,float),deep=True))
    faces=np.asarray(mesh.faces,dtype=np.int64)
    connectivity=np.empty((len(faces),4),dtype=np.int64); connectivity[:,0]=3; connectivity[:,1:]=faces
    cells=vtk.vtkCellArray(); cells.SetCells(len(faces),numpy_to_vtkIdTypeArray(connectivity.ravel(),deep=True))
    poly=vtk.vtkPolyData(); poly.SetPoints(points); poly.SetPolys(cells); return poly

def distances(points, target):
    locator=vtk.vtkStaticCellLocator(); locator.SetDataSet(vtk_poly(target)); locator.BuildLocator()
    out=np.empty(len(points)); cell=vtk.vtkGenericCell()
    for i,p in enumerate(points):
        closest=[0.,0.,0.]; cell_id=vtk.reference(0); sub=vtk.reference(0); dist2=vtk.reference(0.)
        locator.FindClosestPoint(p,closest,cell,cell_id,sub,dist2); out[i]=float(dist2)**0.5
    return out

def sampled_comparison(reference,candidate,samples,seed,mm_per_unit):
    ref_points,_=trimesh.sample.sample_surface(reference,samples,seed=seed)
    can_points,_=trimesh.sample.sample_surface(candidate,samples,seed=seed+1)
    ref_to_can=distances(ref_points,candidate)*mm_per_unit*1000
    can_to_ref=distances(can_points,reference)*mm_per_unit*1000
    both=np.concatenate([ref_to_can,can_to_ref])
    return {"sample_points_each_direction":samples,"mean_symmetric_distance_um":float(both.mean()),
      "p95_symmetric_distance_um":float(np.percentile(both,95)),"sampled_symmetric_hausdorff_um":float(both.max()),
      "reference_to_candidate_p95_um":float(np.percentile(ref_to_can,95)),"candidate_to_reference_p95_um":float(np.percentile(can_to_ref,95))}

def enclosed(points,mesh):
    cloud=vtk.vtkPolyData(); pts=vtk.vtkPoints(); pts.SetData(numpy_to_vtk(points,deep=True)); cloud.SetPoints(pts)
    select=vtk.vtkSelectEnclosedPoints(); select.SetInputData(cloud); select.SetSurfaceData(vtk_poly(mesh)); select.Update()
    return vtk_to_numpy(select.GetOutput().GetPointData().GetArray('SelectedPoints')).astype(bool)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--outdir',type=Path,required=True); ap.add_argument('--secondaries',type=Path)
    ap.add_argument('--samples',type=int,default=20000); ap.add_argument('--seed',type=int,default=20260830); args=ap.parse_args()
    repo=Path(__file__).resolve().parents[2]; args.outdir.mkdir(parents=True,exist_ok=True); scale=0.1
    paths={
      'highres_original':repo/'openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl',
      'decimated_historical':repo/'openworm_geometry/compartment_pipeline/baked_priority_meshes_test/decimated_scoring_surfaces/NervousSystem_baked_union_decimated_150k.stl',
      'voxel_0p020':repo/'openworm_geometry/compartment_pipeline/baked_priority_meshes_test/voxel_remesh_nervous/NervousSystem_baked_union_voxel_0.020.stl',
      'voxel_0p030':repo/'openworm_geometry/compartment_pipeline/baked_priority_meshes_test/voxel_remesh_nervous/NervousSystem_baked_union_voxel_0.030.stl'}
    meshes={}; rows=[]
    for name,path in paths.items(): meshes[name],row=mesh_row(name,path); rows.append(row)
    table=pd.DataFrame(rows); table.to_csv(args.outdir/'nervous_mesh_qc.csv',index=False)
    comparisons=[]
    for name in ['decimated_historical','voxel_0p020','voxel_0p030']:
        comparisons.append({'candidate':name,**sampled_comparison(meshes['highres_original'],meshes[name],args.samples,args.seed,scale)})
    pd.DataFrame(comparisons).to_csv(args.outdir/'nervous_surface_fidelity.csv',index=False)
    scoring=[]
    if args.secondaries:
        df=pd.read_csv(args.secondaries); points=df[['x_um','y_um','z_um']].to_numpy(float)/(scale*1000)
        electrons=df['secondaryPDG'].astype(int).eq(11).to_numpy() if 'secondaryPDG' in df else np.ones(len(df),bool)
        valid=electrons & np.isfinite(points).all(axis=1)
        if 'insideBody' in df: valid &= df['insideBody'].astype(int).eq(1).to_numpy()
        for name in ['voxel_0p020','voxel_0p030']:
            inside=np.zeros(len(df),bool); inside[valid]=enclosed(points[valid],meshes[name])
            scoring.append({'roi':name,'eligible_electrons':int(valid.sum()),'inside_electrons':int(inside.sum()),'inside_fraction':float(inside.sum()/valid.sum()) if valid.any() else 0.})
        pd.DataFrame(scoring).to_csv(args.outdir/'nervous_voxel_scoring_dependence.csv',index=False)
    rng=np.random.default_rng(args.seed); fig,axes=plt.subplots(2,2,figsize=(12,4.5),sharex=True)
    for ax,(name,color) in zip(axes.flat,[('highres_original','black'),('decimated_historical','#377eb8'),('voxel_0p020','#4daf4a'),('voxel_0p030','#e41a1c')]):
        m=meshes[name]; count=min(30000,len(m.vertices)); ids=rng.choice(len(m.vertices),count,replace=False)
        v=m.vertices[ids]*scale*1000; ax.scatter(v[:,1],v[:,0],s=.15,c=color,alpha=.35,rasterized=True)
        ax.set_title(name); ax.set_xlabel('longitudinal y (µm)'); ax.set_ylabel('x (µm)'); ax.set_aspect('equal',adjustable='box')
    fig.suptitle('Nervous representation morphology (same coordinate frame)'); fig.tight_layout()
    fig.savefig(args.outdir/'nervous_morphology_qc.png',dpi=300); fig.savefig(args.outdir/'nervous_morphology_qc.svg')
    summary={'mm_per_model_unit':scale,'mesh_rows':rows,'surface_comparisons':comparisons,'voxel_scoring':scoring,
      'volume_ratio_voxel_0p030_to_0p020':float(meshes['voxel_0p030'].volume/meshes['voxel_0p020'].volume)}
    (args.outdir/'geometry_qc_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
