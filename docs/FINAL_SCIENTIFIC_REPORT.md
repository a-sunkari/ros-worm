# ROS-Worm v1 scientific summary for review

## Question and scope

ROS-Worm connects OpenWorm anatomy to Geant4 X-ray transport and Geant4-DNA
water radiolysis under approximations to the Cannon/Bolding *C. elegans* X-ray
experiments. The workflow asks where energy deposition and secondary-electron
births occur, and how often those births lie near neural anatomy. It does not
claim to predict LITE-1 activation.

## Model decision

The nervous anatomy cannot presently support a true absorbed-dose tally. Its
1.36-million-face aggregate preserves fine morphology but is open and
non-manifold. Two watertight voxelizations changed volume by 65.5%, introduced
21–33 µm p95 surface error, and changed inside classification nearly threefold.
The accepted neural result is therefore exact closest-surface distance from
finite, in-body secondary-electron birth positions to the original atlas. It is
reported explicitly as proximity, never nervous absorbed dose.

Physical transport uses a residual soft-tissue body plus body-wall muscle,
digestive, and reproductive daughters. Excretory anatomy remains a scoring ROI
but is not a physical same-material daughter because that boundary generated the
historic navigator failure and impossible coordinate.

## Production results

At 10M histories, focused 50-kV transport produced 90,514 eligible electron
births and diffuse 20-kV transport produced 62,968. The fractions within 5 µm of
the neural surface were 7.250% and 6.441%; median distances were 35.36 and
37.19 µm. No eligible birth was outside the body. Regional energy deposition was
dominated by residual body tissue (~95%), with reproducible percent-level
fractions in muscle, digestive, and reproductive compartments.

The focused/diffuse runs produced 18/3 navigation incidents in 10M histories.
Those remaining body/organ boundary pushes are disclosed and had no observed
effect on output validity. Removing additional boundaries would trade anatomical
fidelity for a warning count without demonstrated scientific benefit.

Near-neural electron spectra were sampled in two 10k-event homogeneous-water
chemistry runs. At 1 µs, predicted •OH G values were 1.363/1.337 and H2O2 G values
were 0.916/0.922 molecules per 100 eV for focused/diffuse inputs. These values
describe the implemented Geant4-DNA reaction system, not biological ROS amounts.

## What is supported

- A reproducible focused-50-kV and diffuse-20-kV OpenWorm transport workflow.
- Regional physical energy-deposition fractions and per-history dose tallies.
- Exact full-resolution neural-surface proximity of valid electron births.
- Quantitative rejection of current voxel nervous volumes.
- Audited navigation warnings and explicit out-of-body filtering semantics.
- Spectrum-driven homogeneous-water radiolysis G values.

## What remains approximate

- Kramers endpoints substitute for measured tungsten/silver spectral and spatial
  distributions; absolute normalization inherits the experimental dosimetry
  uncertainty (reported by Cannon et al. as approximately a factor of two for
  focused exposure).
- The stable whole-body envelope and material assignments are organ-scale
  approximations; agar/M9/container are absent.
- Neural proximity is not inside-neuron transport, neural absorbed dose, or a
  biological activation probability.
- Independent electron-source chemistry loses the original spatial track and
  biological chemical environment.

The appropriate next experimental-modeling advance is better characterized beam
input and biological chemistry/segmentation data, not more aggressive STL repair.
