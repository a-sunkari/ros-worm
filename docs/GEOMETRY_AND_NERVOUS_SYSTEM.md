# Geometry and nervous-system treatment

## Physical transport geometry

`ros_worm_stage1/config/transport_geometry_v1.csv` is authoritative. Its paths,
hashes, counts, and bounds were recomputed from the referenced STL contents.
Geant4 centers every mesh using the actual body-envelope center and uses:

- WholeBodyEnvelope as residual soft tissue;
- BodyWallMuscle, DigestiveSystem, and ReproductiveSystem as daughters;
- no physical nervous daughter;
- no physical excretory daughter.

The residual-body scoring mass is the mother volume minus physical daughter
volumes, eliminating the former parent/child mass double count.

## Neural decision

The original OpenWorm neural aggregate is a high-detail surface atlas, not a
valid closed solid. Making a watertight mesh was not treated as sufficient.
`scripts/qc_geometry_v1.py` compares candidates by bounds, morphology,
connectivity, topology, sampled symmetric surface distance, and scoring impact.

| representation | faces | components | watertight | sampled symmetric p95 error | reference→candidate p95 |
|---|---:|---:|:---:|---:|---:|
| original high resolution | 1,355,686 | 54 | no | reference | reference |
| historical decimation | 522,169 | 937 | no | 3.23 µm | 7.10 µm |
| voxel 0.020 | 7,026 | 241 | yes | 15.53 µm | 21.16 µm |
| voxel 0.030 | 3,442 | 125 | yes | 24.53 µm | 33.45 µm |

The sampled maximum symmetric distances were 19.0, 42.9, and 48.4 µm,
respectively. In the same 90,514-electron focused dataset, the two voxel volumes
classified 59 and 173 births as inside. The near-threefold scoring difference
and 65.5% volume difference reject these meshes as a converged volumetric ROI.

The authoritative neural endpoint is therefore exact distance from an eligible
secondary-electron birth to the **original full-resolution triangle surface**,
implemented in `scripts/score_nervous_surface_v1.py` using
`vtkStaticCellLocator`. Threshold shells (0.5–50 µm) remain interpretable despite
the open surface. They do not define an inside volume and are not absorbed dose.

## Coordinate alignment

At 0.1 mm/model unit, physical body bounds are ±41.34 µm (x), ±439.72 µm (y),
and ±95.07 µm (z). Neural bounds are -28.98 to 27.62 µm, -349.54 to 448.32 µm,
and -67.09 to 64.91 µm. Both transport and scorer derive placement from the
actual body STL. This corrects the historical ~50.9-µm y displacement created
by stale manifest bounds.

## Non-neural warnings

The historical excretory daughter was very small, disconnected, and assigned
the same material as residual body. Direct inspection of the prior 10M ROOT file
showed that its navigation failures created the extreme secondary coordinate.
Omitting it physically removes a material-neutral boundary while retaining the
mesh for post-processing ROI use.

The new focused/diffuse 10M runs have 18/3 remaining warning incidents,
respectively. These occur at body/digestive, body/body-wall, and one
body/reproductive interface. Further destructive smoothing was not justified by
this low rate, because the current failures no longer contaminate saved electron
birth positions. Warning summaries remain mandatory for every run.

## Rules for future neural-volume work

A future implicit ROI may supersede proximity only after voxel/radius convergence,
quantitative distance and morphology comparison, stable scoring, and—if made
physical—clean Geant4 navigation. Do not infer anatomical fidelity from
watertightness and do not overwrite any source STL.
