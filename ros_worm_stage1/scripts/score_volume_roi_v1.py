#!/usr/bin/env python3
"""Postprocess energy-deposition points and electron births inside a watertight ROI."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

def polydata(path, center, scale):
    reader=vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    mesh=vtk.vtkPolyData(); mesh.DeepCopy(reader.GetOutput())
    values=vtk_to_numpy(mesh.GetPoints().GetData()).astype(float,copy=True)
    values=(values-center[None,:])*scale
    points=vtk.vtkPoints(); points.SetData(numpy_to_vtk(values,deep=True)); mesh.SetPoints(points)
    return mesh

def inside(points, surface):
    cloud=vtk.vtkPolyData(); vtk_points=vtk.vtkPoints(); vtk_points.SetData(numpy_to_vtk(points,deep=True)); cloud.SetPoints(vtk_points)
    selector=vtk.vtkSelectEnclosedPoints(); selector.SetInputData(cloud); selector.SetSurfaceData(surface); selector.SetTolerance(1e-8); selector.Update()
    return vtk_to_numpy(selector.GetOutput().GetPointData().GetArray('SelectedPoints')).astype(bool)

def body_center(manifest):
    table=pd.read_csv(manifest); row=table[table.safe_name.eq('WholeBodyEnvelope')].iloc[0]
    path=Path(row.stl_path); path=path if path.is_absolute() else (manifest.parent/path).resolve()
    reader=vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    bounds=np.asarray(reader.GetOutput().GetBounds()).reshape(3,2); return bounds.mean(axis=1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--steps-npz',type=Path,required=True); ap.add_argument('--secondaries',type=Path,required=True)
    ap.add_argument('--roi-stl',type=Path,required=True); ap.add_argument('--roi-name',required=True); ap.add_argument('--placement-manifest',type=Path,required=True)
    ap.add_argument('--outdir',type=Path,required=True); ap.add_argument('--mm-per-model-unit',type=float,default=.1); args=ap.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True); center=body_center(args.placement_manifest)
    surface=polydata(args.roi_stl,center,args.mm_per_model_unit)
    loaded=np.load(args.steps_npz); arrays={name:loaded[name] for name in loaded.files}
    step_points=np.column_stack([arrays['x_um'],arrays['y_um'],arrays['z_um']])*1e-3
    step_inside=inside(step_points,surface)
    secondaries=pd.read_csv(args.secondaries); sec_points=secondaries[['x_um','y_um','z_um']].to_numpy(float)*1e-3
    electron=secondaries.secondaryPDG.astype(int).eq(11).to_numpy() if 'secondaryPDG' in secondaries else np.ones(len(secondaries),bool)
    sec_inside=np.zeros(len(secondaries),bool); sec_inside[electron]=inside(sec_points[electron],surface)
    secondaries['inside_'+args.roi_name]=sec_inside
    secondaries[sec_inside].to_csv(args.outdir/f'electrons_inside_{args.roi_name}.csv',index=False)
    edep=np.asarray(arrays['edep_keV'],float)
    summary={'method':'postprocessed point classification in a watertight ROI; deposition assigned by pre-step point',
      'roi_name':args.roi_name,'roi_stl':str(args.roi_stl.resolve()),'steps_npz':str(args.steps_npz.resolve()),
      'n_edep_steps':int(len(edep)),'n_edep_steps_inside_roi':int(step_inside.sum()),'edep_keV_inside_roi':float(edep[step_inside].sum()),
      'n_electron_creation_points':int(electron.sum()),'n_electron_creation_points_inside_roi':int(sec_inside.sum()),
      'fraction_electron_creation_points_inside_roi':float(sec_inside.sum()/electron.sum()) if electron.any() else 0.0,
      'roi_bounds_mm':list(surface.GetBounds()),'body_center_model_units':center.tolist()}
    (args.outdir/f'{args.roi_name}_roi_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
