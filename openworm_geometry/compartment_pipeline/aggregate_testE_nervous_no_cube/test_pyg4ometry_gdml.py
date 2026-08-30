from pathlib import Path
import pyg4ometry as pg4

gdml = Path("/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/openworm_priority_resolved.gdml")
outdir = gdml.parent / "pyg4ometry_export"
outdir.mkdir(exist_ok=True)

print("[pyg4ometry] reading:", gdml)
reader = pg4.gdml.Reader(str(gdml))
reg = reader.getRegistry()
world = reg.getWorldVolume()
print("[pyg4ometry] world:", world.name)

print("[pyg4ometry] logical volumes:", len(reg.logicalVolumeDict))
print("[pyg4ometry] solids:", len(reg.solidDict))

print("[pyg4ometry] exporting VTP scene...")
viewer = pg4.visualisation.VtkViewer()
viewer.addLogicalVolume(world)
viewer.exportVTPScene(str(outdir / "openworm_priority_resolved"))

print("[pyg4ometry] wrote:", outdir)
