from pathlib import Path
import sys
import numpy as np
import trimesh
import pyvista as pv

if len(sys.argv) < 2:
    print("Usage: python qc_stl_visual.py /path/to/mesh.stl")
    sys.exit(1)

path = Path(sys.argv[1]).expanduser().resolve()
print("Loading:", path)

mesh = trimesh.load_mesh(path, force="mesh", process=True)
mesh.merge_vertices()
mesh.remove_unreferenced_vertices()

print("\n===== BASIC STATS =====")
print("faces:", len(mesh.faces))
print("verts:", len(mesh.vertices))
print("watertight:", mesh.is_watertight)
print("winding_consistent:", mesh.is_winding_consistent)
print("volume:", mesh.volume)
print("bounds:", mesh.bounds.tolist())
components = mesh.split(only_watertight=False)
print("components:", len(components))

# --- Build PyVista surface ---
faces_pv = np.hstack(
    [np.full((len(mesh.faces), 1), 3, dtype=np.int64), mesh.faces.astype(np.int64)]
)
surf = pv.PolyData(mesh.vertices, faces_pv)

# --- Edge count analysis ---
edges_unique = mesh.edges_unique
inv = mesh.edges_unique_inverse
counts = np.bincount(inv, minlength=len(edges_unique))

boundary_edges = edges_unique[counts == 1]      # holes / open boundaries
nonmanifold_edges = edges_unique[counts > 2]    # topological trouble

print("\n===== EDGE DEFECTS =====")
print("boundary edge count:", len(boundary_edges))
print("nonmanifold edge count:", len(nonmanifold_edges))

def edges_to_polydata(vertices, edges):
    if len(edges) == 0:
        return None
    lines = np.hstack(
        [np.full((len(edges), 1), 2, dtype=np.int64), edges.astype(np.int64)]
    ).ravel()
    return pv.PolyData(vertices, lines=lines)

boundary_poly = edges_to_polydata(mesh.vertices, boundary_edges)
nonmanifold_poly = edges_to_polydata(mesh.vertices, nonmanifold_edges)

# --- Broken faces from trimesh repair helpers ---
broken_faces_idx = None
try:
    broken_faces_idx = trimesh.repair.broken_faces(mesh)
    if broken_faces_idx is None:
        broken_faces_idx = np.array([], dtype=int)
    broken_faces_idx = np.asarray(broken_faces_idx, dtype=int)
except Exception:
    broken_faces_idx = np.array([], dtype=int)

print("broken face count:", len(broken_faces_idx))

broken_poly = None
if len(broken_faces_idx) > 0:
    broken_poly = surf.extract_cells(broken_faces_idx)

# --- Largest connected components as separate colors ---
component_meshes = []
for comp in sorted(components, key=lambda m: len(m.faces), reverse=True)[:20]:
    if len(comp.faces) == 0:
        continue
    comp_faces = np.hstack(
        [np.full((len(comp.faces), 1), 3, dtype=np.int64), comp.faces.astype(np.int64)]
    )
    component_meshes.append(pv.PolyData(comp.vertices, comp_faces))

# --- Plot ---
pl = pv.Plotter(window_size=(1400, 1000))
pl.add_axes()
pl.add_text(str(path.name), font_size=12)

# Main mesh
pl.add_mesh(surf, color="lightgray", opacity=0.35, show_edges=False)

# Overlay largest components with different colors
for i, comp_poly in enumerate(component_meshes):
    pl.add_mesh(comp_poly, opacity=0.20, show_edges=False)

# Defect overlays
if boundary_poly is not None:
    pl.add_mesh(boundary_poly, color="red", line_width=6, label="Boundary edges (holes)")
if nonmanifold_poly is not None:
    pl.add_mesh(nonmanifold_poly, color="yellow", line_width=8, label="Non-manifold edges")
if broken_poly is not None and broken_poly.n_cells > 0:
    pl.add_mesh(broken_poly, color="magenta", opacity=1.0, label="Broken faces")

pl.add_legend()
pl.show_grid()
pl.show()