#!/usr/bin/env python3
"""Fast ROOT-to-NumPy bridge kept separate to avoid ROOT/VTK libcurl conflicts."""
import argparse
from pathlib import Path
import numpy as np
import ROOT

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root_file'); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    arrays=ROOT.RDataFrame('steps',args.root_file).AsNumpy(['edep_keV','x_um','y_um','z_um','pdg'])
    args.output.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(args.output,**arrays); print(args.output)

if __name__=='__main__': main()
