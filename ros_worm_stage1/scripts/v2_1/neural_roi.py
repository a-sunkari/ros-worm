#!/usr/bin/env python3
"""Shared analysis-only nervous-ROI utilities for ROS-Worm v2.1.

The original atlas aggregate is not a closed solid.  The source object manifest,
however, identifies 276 individually repaired, closed nervous objects.  Their
set-theoretic union is a valid analysis ROI without performing a destructive
Boolean union or placing nervous anatomy in Geant4.  This module implements that
union and sparse, grid-convergent voxel approximations of it.
"""
from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy


def resolve_repo_path(value: str | Path, repo: Path) -> Path:
    """Resolve legacy absolute paths after a repository has moved."""
    path = Path(value)
    text = str(path)
    marker = "/openworm_geometry/"
    if marker in text:
        candidate = repo / ("openworm_geometry/" + text.split(marker, 1)[1])
        if candidate.exists():
            return candidate.resolve()
    marker = "/ros_worm_stage1/"
    if marker in text:
        candidate = repo / ("ros_worm_stage1/" + text.split(marker, 1)[1])
        if candidate.exists():
            return candidate.resolve()
    if path.exists():
        return path.resolve()
    if not path.is_absolute():
        candidate = repo / path
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"Cannot resolve atlas member path: {value}")


def stl_polydata(path: Path, center_model: np.ndarray, um_per_model_unit: float) -> vtk.vtkPolyData:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    if reader.GetOutput().GetNumberOfCells() == 0:
        raise ValueError(f"STL has no cells: {path}")
    mesh = vtk.vtkPolyData()
    mesh.DeepCopy(reader.GetOutput())
    points = vtk_to_numpy(mesh.GetPoints().GetData()).astype(np.float64, copy=True)
    points = (points - center_model[None, :]) * um_per_model_unit
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(points, deep=True))
    mesh.SetPoints(vtk_points)
    mesh.BuildCells()
    mesh.BuildLinks()
    return mesh


def body_center_and_path(placement_manifest: Path, repo: Path) -> tuple[np.ndarray, Path]:
    table = pd.read_csv(placement_manifest)
    body = table[(table["safe_name"] == "WholeBodyEnvelope") |
                 (table["category_guess"] == "whole_body_parent")]
    if len(body) != 1:
        raise ValueError(f"Expected one whole-body row; found {len(body)}")
    path = resolve_repo_path(str(body.iloc[0]["stl_path"]), repo)
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    bounds = np.asarray(reader.GetOutput().GetBounds(), dtype=float).reshape(3, 2)
    return bounds.mean(axis=1), path


def member_table(source_manifest: Path) -> pd.DataFrame:
    table = pd.read_csv(source_manifest)
    members = table[table["category_guess"] == "NervousSystem"].copy()
    if len(members) == 0:
        raise ValueError(f"No NervousSystem rows in {source_manifest}")
    return members.reset_index(drop=True)


def load_member_surfaces(source_manifest: Path, placement_manifest: Path, repo: Path,
                         um_per_model_unit: float = 100.0) -> tuple[list[dict], np.ndarray, vtk.vtkPolyData]:
    center, body_path = body_center_and_path(placement_manifest, repo)
    surfaces: list[dict] = []
    for row in member_table(source_manifest).itertuples(index=False):
        path = resolve_repo_path(row.stl_path, repo)
        mesh = stl_polydata(path, center, um_per_model_unit)
        surfaces.append({"name": str(row.object_name), "path": path, "mesh": mesh,
                         "bounds_um": np.asarray(mesh.GetBounds()).reshape(3, 2)})
    body = stl_polydata(body_path, center, um_per_model_unit)
    return surfaces, center, body


def enclosed_points(points_um: np.ndarray, surface: vtk.vtkPolyData) -> np.ndarray:
    if len(points_um) == 0:
        return np.zeros(0, dtype=bool)
    cloud = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(np.ascontiguousarray(points_um, dtype=np.float64), deep=True))
    cloud.SetPoints(vtk_points)
    selector = vtk.vtkSelectEnclosedPoints()
    selector.SetInputData(cloud)
    selector.SetSurfaceData(surface)
    selector.SetTolerance(1e-7)
    selector.Update()
    values = vtk_to_numpy(selector.GetOutput().GetPointData().GetArray("SelectedPoints"))
    return values.astype(bool)


def closest_surface_distances(points_um: np.ndarray, surface: vtk.vtkPolyData,
                              workers: int = 1) -> np.ndarray:
    """Exact unsigned point-to-triangle distance using a shared static locator."""
    points = np.asarray(points_um, dtype=float)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(surface)
    locator.BuildLocator()
    result = np.empty(len(points), dtype=np.float32)

    def score(start_stop: tuple[int, int]) -> None:
        start, stop = start_stop
        cell = vtk.vtkGenericCell()
        for index in range(start, stop):
            target = [0.0, 0.0, 0.0]
            cell_id, sub_id, distance2 = vtk.reference(0), vtk.reference(0), vtk.reference(0.0)
            locator.FindClosestPoint(points[index], target, cell, cell_id, sub_id, distance2)
            result[index] = float(distance2) ** 0.5

    workers = max(1, min(int(workers), len(points) or 1))
    edges = np.linspace(0, len(points), workers + 1, dtype=int)
    chunks = [(int(edges[i]), int(edges[i + 1])) for i in range(workers) if edges[i] < edges[i + 1]]
    if workers == 1:
        score(chunks[0] if chunks else (0, 0))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            list(executor.map(score, chunks))
    return result


_WORKER_LOCATOR = None


def _distance_worker_init(stl_path: str, center_model: np.ndarray, um_per_model_unit: float) -> None:
    global _WORKER_LOCATOR
    surface = stl_polydata(Path(stl_path), np.asarray(center_model), um_per_model_unit)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(surface)
    locator.BuildLocator()
    # Keep both objects alive; the locator references its data set.
    _WORKER_LOCATOR = (surface, locator)


def _distance_worker(points: np.ndarray) -> np.ndarray:
    if _WORKER_LOCATOR is None:
        raise RuntimeError("Distance worker was not initialized")
    _, locator = _WORKER_LOCATOR
    result = np.empty(len(points), dtype=np.float32)
    cell = vtk.vtkGenericCell()
    for index, point in enumerate(points):
        target = [0.0, 0.0, 0.0]
        cell_id, sub_id, distance2 = vtk.reference(0), vtk.reference(0), vtk.reference(0.0)
        locator.FindClosestPoint(point, target, cell, cell_id, sub_id, distance2)
        result[index] = float(distance2) ** 0.5
    return result


def closest_surface_distances_file(points_um: np.ndarray, stl_path: Path,
                                   center_model: np.ndarray, um_per_model_unit: float = 100.0,
                                   workers: int = 1) -> np.ndarray:
    """Parallel exact distance queries; each process owns its VTK locator."""
    points = np.asarray(points_um, dtype=float)
    workers = max(1, min(int(workers), len(points) or 1))
    if workers == 1:
        surface = stl_polydata(stl_path, center_model, um_per_model_unit)
        return closest_surface_distances(points, surface, 1)
    chunks = [chunk for chunk in np.array_split(points, workers) if len(chunk)]
    context = mp.get_context("spawn")
    with context.Pool(workers, initializer=_distance_worker_init,
                      initargs=(str(stl_path), np.asarray(center_model), um_per_model_unit)) as pool:
        parts = pool.map(_distance_worker, chunks)
    return np.concatenate(parts)


def inside_member_union(points_um: np.ndarray, members: list[dict], chunk_size: int = 250_000) -> np.ndarray:
    """Classify points inside any closed source member, using AABBs as broad phase."""
    points = np.asarray(points_um, dtype=float)
    result = np.zeros(len(points), dtype=bool)
    finite = np.isfinite(points).all(axis=1)
    for item in members:
        bounds = item["bounds_um"]
        candidate = finite & ~result & np.all(points >= bounds[:, 0], axis=1) & np.all(points <= bounds[:, 1], axis=1)
        indices = np.flatnonzero(candidate)
        for start in range(0, len(indices), chunk_size):
            chosen = indices[start:start + chunk_size]
            result[chosen] = enclosed_points(points[chosen], item["mesh"])
    return result


@dataclass(frozen=True)
class SparseVoxelROI:
    pitch_um: float
    origin_edge_um: np.ndarray
    dimensions: np.ndarray
    flat_indices: np.ndarray

    @classmethod
    def load(cls, path: Path) -> "SparseVoxelROI":
        data = np.load(path)
        return cls(float(data["pitch_um"]), data["origin_edge_um"].astype(float),
                   data["dimensions"].astype(np.int64), data["flat_indices"].astype(np.int64))

    def contains(self, points_um: np.ndarray) -> np.ndarray:
        points = np.asarray(points_um, dtype=float)
        ijk = np.floor((points - self.origin_edge_um[None, :]) / self.pitch_um).astype(np.int64)
        valid = np.isfinite(points).all(axis=1) & np.all(ijk >= 0, axis=1) & np.all(ijk < self.dimensions, axis=1)
        flat = ijk[:, 0] + self.dimensions[0] * (ijk[:, 1] + self.dimensions[1] * ijk[:, 2])
        positions = np.searchsorted(self.flat_indices, flat)
        found = valid & (positions < len(self.flat_indices))
        found[found] &= self.flat_indices[positions[found]] == flat[found]
        return found

    def centers(self, selected_flat: np.ndarray | None = None) -> np.ndarray:
        flat = self.flat_indices if selected_flat is None else np.asarray(selected_flat, dtype=np.int64)
        nx, ny, _ = self.dimensions
        iz = flat // (nx * ny)
        remainder = flat - iz * nx * ny
        iy = remainder // nx
        ix = remainder - iy * nx
        return self.origin_edge_um + (np.column_stack([ix, iy, iz]) + 0.5) * self.pitch_um


def grid_definition(bounds_um: np.ndarray, pitch_um: float) -> tuple[np.ndarray, np.ndarray]:
    lower_index = np.floor(bounds_um[:, 0] / pitch_um).astype(np.int64) - 1
    upper_index = np.ceil(bounds_um[:, 1] / pitch_um).astype(np.int64) + 1
    origin_edge = lower_index * pitch_um
    dimensions = upper_index - lower_index
    return origin_edge.astype(float), dimensions.astype(np.int64)


def voxelize_member(member: dict, pitch_um: float, origin_edge_um: np.ndarray,
                    dimensions: np.ndarray) -> np.ndarray:
    """Return globally indexed occupied voxel centers for one closed member."""
    origin_center = origin_edge_um + 0.5 * pitch_um
    bounds = member["bounds_um"]
    lower = np.floor((bounds[:, 0] - origin_center) / pitch_um).astype(np.int64) - 1
    upper = np.ceil((bounds[:, 1] - origin_center) / pitch_um).astype(np.int64) + 1
    lower = np.maximum(lower, 0)
    upper = np.minimum(upper, dimensions - 1)
    extent = [int(lower[0]), int(upper[0]), int(lower[1]), int(upper[1]),
              int(lower[2]), int(upper[2])]

    stencil = vtk.vtkPolyDataToImageStencil()
    stencil.SetInputData(member["mesh"])
    stencil.SetOutputOrigin(*origin_center)
    stencil.SetOutputSpacing(pitch_um, pitch_um, pitch_um)
    stencil.SetOutputWholeExtent(*extent)
    stencil.SetTolerance(1e-7)
    stencil.Update()

    convert = vtk.vtkImageStencilToImage()
    convert.SetInputConnection(stencil.GetOutputPort())
    convert.SetInsideValue(1)
    convert.SetOutsideValue(0)
    convert.SetOutputScalarTypeToUnsignedChar()
    convert.Update()
    image = convert.GetOutput()
    values = vtk_to_numpy(image.GetPointData().GetScalars())
    local = np.flatnonzero(values)
    if len(local) == 0:
        return np.zeros(0, dtype=np.int64)
    local_dims = np.asarray(image.GetDimensions(), dtype=np.int64)
    lz = local // (local_dims[0] * local_dims[1])
    rem = local - lz * local_dims[0] * local_dims[1]
    ly = rem // local_dims[0]
    lx = rem - ly * local_dims[0]
    ix = lx + lower[0]
    iy = ly + lower[1]
    iz = lz + lower[2]
    return (ix + dimensions[0] * (iy + dimensions[1] * iz)).astype(np.int64)


def sparse_connectivity(flat_indices: np.ndarray, dimensions: np.ndarray) -> tuple[int, np.ndarray, np.ndarray]:
    """26-connected components and a six-neighbor boundary mask, sparsely."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    occupied = np.asarray(flat_indices, dtype=np.int64)
    nx, ny, _ = dimensions
    ix = occupied % nx
    iy = (occupied // nx) % ny
    iz = occupied // (nx * ny)
    nz = dimensions[2]
    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    six_neighbor_count = np.zeros(len(occupied), dtype=np.uint8)
    half_neighbors = []
    for dz in range(0, 2):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dz == 0 and (dy < 0 or (dy == 0 and dx <= 0)):
                    continue
                if dx == dy == dz == 0:
                    continue
                half_neighbors.append((dx, dy, dz))
    for dx, dy, dz in half_neighbors:
        mask = ((ix + dx >= 0) & (ix + dx < nx) &
                (iy + dy >= 0) & (iy + dy < ny) &
                (iz + dz >= 0) & (iz + dz < nz))
        delta = dx + nx * (dy + ny * dz)
        row_candidates = np.flatnonzero(mask)
        target = occupied[row_candidates] + delta
        positions = np.searchsorted(occupied, target)
        found = positions < len(occupied)
        found[found] &= occupied[positions[found]] == target[found]
        left = row_candidates[found]
        right = positions[found]
        rows.extend([left, right])
        cols.extend([right, left])
        if abs(dx) + abs(dy) + abs(dz) == 1:
            six_neighbor_count[left] += 1
            six_neighbor_count[right] += 1
    if rows:
        row = np.concatenate(rows)
        col = np.concatenate(cols)
        graph = coo_matrix((np.ones(len(row), dtype=np.uint8), (row, col)),
                           shape=(len(occupied), len(occupied))).tocsr()
        count, labels = connected_components(graph, directed=False)
    else:
        count = len(occupied)
        labels = np.arange(len(occupied), dtype=np.int32)
    return int(count), np.bincount(labels), six_neighbor_count < 6
