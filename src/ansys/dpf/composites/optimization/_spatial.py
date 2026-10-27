# Copyright (C) 2022 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Connectivity-constrained local ply-extent pruning for spatial optimization."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import replace
from math import isfinite

from ._models import Laminate, _finite
from ._problem import CandidateEvaluation


def _components(nodes: set[int], neighbors: Mapping[int, frozenset[int]]) -> tuple[frozenset[int], ...]:
    """Return deterministic connected components of the induced element graph."""
    remaining = set(nodes)
    result = []
    while remaining:
        seed = min(remaining)
        component = {seed}
        frontier = [seed]
        remaining.remove(seed)
        while frontier:
            element_id = frontier.pop()
            for neighbor in neighbors[element_id] & remaining:
                remaining.remove(neighbor)
                component.add(neighbor)
                frontier.append(neighbor)
        result.append(frozenset(component))
    return tuple(result)


def _is_connected(nodes: set[int], neighbors: Mapping[int, frozenset[int]]) -> bool:
    """Whether a nonempty element set is connected using supplied adjacency."""
    if len(nodes) <= 1:
        return True
    return len(_components(nodes, neighbors)) == 1


class SpatialPlyExtentOptimizer:
    """Greedily minimize local ply extents while preserving feasibility/connectivity.

    Parameters
    ----------
    element_neighbors:
        Undirected adjacency graph keyed by every optimized element ID. Supply
        edge-sharing neighbors for shell meshes (and face-sharing neighbors for
        solids); node-only/diagonal contact does not count as continuous. The
        graph must cover exactly the sampling-point elements being optimized.
    element_weights:
        Optional positive element areas or other physical integration weights.
        Defaults to each Laminate's ``weight``. The inner pruning chooses the
        feasible removal with the largest reduction in weighted mass per area.
    minimum_plies:
        Minimum plies retained in every local laminate.
    offset_policy:
        Keep the reference bottom fixed or recenter the laminate mid-plane after
        each local thickness reduction.
    max_evaluations:
        Bound the number of unique local-mask evaluations for one global design.
        If reached, the best feasible mask is returned with
        ``extent_search_complete=False`` on its CandidateEvaluation.

    Notes
    -----
    This is a deterministic greedy inner optimizer, not an exact solution of
    the joint binary mask problem. It starts with the supplied per-element masks
    and only removes plies. For each ply, every original connected component is
    allowed to shrink to empty or remain connected; a removal that splits one
    into multiple islands is rejected. This prevents detached/checkerboard
    islands under edge-sharing adjacency. It does not create plies on elements
    where they were initially absent. User IRF constraints and custom problem
    constraints are checked after every trial removal.
    """

    def __init__(
        self,
        element_neighbors: Mapping[int, Collection[int]],
        *,
        element_weights: Mapping[int, float] | None = None,
        minimum_plies: int = 1,
        offset_policy: str = "midplane",
        max_evaluations: int = 5000,
    ) -> None:
        if not element_neighbors:
            raise ValueError("element_neighbors must not be empty.")
        self.element_ids = tuple(sorted(element_neighbors))
        node_set = set(self.element_ids)
        neighbors = {element_id: frozenset(values) for element_id, values in element_neighbors.items()}
        for element_id, adjacent in neighbors.items():
            if element_id in adjacent:
                raise ValueError(f"Element {element_id} cannot be its own neighbor.")
            if adjacent - node_set:
                raise ValueError(f"Neighbors of element {element_id} are missing from the graph.")
            if any(element_id not in neighbors[other] for other in adjacent):
                raise ValueError("element_neighbors must describe an undirected adjacency graph.")
        self.neighbors = neighbors
        if element_weights is None:
            self.element_weights = None
        else:
            if set(element_weights) != node_set:
                raise ValueError("element_weights must cover exactly the adjacency graph elements.")
            weights = {int(key): float(value) for key, value in element_weights.items()}
            for element_id, weight in weights.items():
                _finite(weight, f"element_weights[{element_id}]", positive=True)
            self.element_weights = weights
        if isinstance(minimum_plies, bool) or not isinstance(minimum_plies, int) or minimum_plies < 1:
            raise ValueError("minimum_plies must be a positive integer.")
        if offset_policy not in ("bottom", "midplane"):
            raise ValueError("offset_policy must be 'bottom' or 'midplane'.")
        if isinstance(max_evaluations, bool) or not isinstance(max_evaluations, int) or max_evaluations < 1:
            raise ValueError("max_evaluations must be a positive integer.")
        self.minimum_plies = minimum_plies
        self.offset_policy = offset_policy
        self.max_evaluations = max_evaluations
        self._weights: Mapping[int, float] = {}

    @staticmethod
    def _signature(laminates: Sequence[Laminate]) -> tuple[tuple[str, ...], ...]:
        """Mask signature; properties do not change during the inner search."""
        return tuple(tuple(p.id for p in laminate.plies) for laminate in laminates)

    def _weighted_mass(self, assessment: CandidateEvaluation) -> float:
        mass_by_point: dict[str, float] = {}
        for result in assessment.results:
            mass_by_point.setdefault(result.point, result.response.mass_per_unit_area)
        return sum(
            self._weights[laminate.element_id] * mass_by_point[laminate.name]
            for laminate in assessment.laminates
        )

    def optimize(
        self,
        laminates: tuple[Laminate, ...],
        assess: Callable[[tuple[Laminate, ...]], CandidateEvaluation],
        *,
        feasibility_tolerance: float = 1e-8,
    ) -> CandidateEvaluation:
        """Return a feasible locally pruned candidate using supplied connectivity."""
        points = tuple(laminates)
        point_ids = [point.element_id for point in points]
        if len(point_ids) != len(set(point_ids)):
            raise ValueError("Spatial extent optimization requires one laminate per element ID.")
        if set(point_ids) != set(self.element_ids):
            raise ValueError("Adjacency graph elements must match the optimized sampling points.")
        if not isfinite(feasibility_tolerance) or feasibility_tolerance < 0:
            raise ValueError("feasibility_tolerance must be finite and nonnegative.")
        self._weights = (
            self.element_weights
            if self.element_weights is not None
            else {point.element_id: point.weight for point in points}
        )
        ply_ids = tuple(dict.fromkeys(ply.id for point in points for ply in point.plies))
        original_components = {
            ply_id: _components(
                {
                    point.element_id
                    for point in points
                    if any(ply.id == ply_id for ply in point.plies)
                },
                self.neighbors,
            )
            for ply_id in ply_ids
        }
        cache: dict[tuple[tuple[str, ...], ...], CandidateEvaluation] = {}
        evaluations = 0

        def get_assessment(candidate: tuple[Laminate, ...]) -> CandidateEvaluation:
            nonlocal evaluations
            signature = self._signature(candidate)
            if signature not in cache:
                cache[signature] = assess(candidate)
                evaluations += 1
            return cache[signature]

        current_laminates = tuple(
            replace(point, weight=self._weights[point.element_id]) for point in points
        )
        current_assessment = get_assessment(current_laminates)
        if current_assessment.invalid_reason is not None or current_assessment.max_violation > feasibility_tolerance:
            return replace(
                current_assessment,
                extent_search_complete=True,
                extent_removals=(),
                extent_evaluations=evaluations,
            )

        removed: list[tuple[int, str]] = []
        complete = True
        while True:
            current_mass = self._weighted_mass(current_assessment)
            best_move: tuple[float, int, str, tuple[Laminate, ...], CandidateEvaluation] | None = None
            for ply_id in ply_ids:
                active = {
                    point.element_id
                    for point in current_laminates
                    if any(ply.id == ply_id for ply in point.plies)
                }
                if not active:
                    continue
                for element_id in sorted(active):
                    point = next(
                        laminate
                        for laminate in current_laminates
                        if laminate.element_id == element_id
                    )
                    if len(point.plies) <= self.minimum_plies:
                        continue
                    remaining = active - {element_id}
                    if any(
                        component & remaining
                        and not _is_connected(set(component & remaining), self.neighbors)
                        for component in original_components[ply_id]
                    ):
                        continue
                    removed_ply = next(ply for ply in point.plies if ply.id == ply_id)
                    candidate_point = replace(
                        point,
                        plies=tuple(ply for ply in point.plies if ply.id != ply_id),
                        offset=(
                            point.offset + removed_ply.thickness / 2
                            if self.offset_policy == "midplane"
                            else point.offset
                        ),
                    )
                    candidate = tuple(
                        candidate_point if other.element_id == element_id else other
                        for other in current_laminates
                    )
                    signature = self._signature(candidate)
                    if signature not in cache and evaluations >= self.max_evaluations:
                        complete = False
                        break
                    assessment = get_assessment(candidate)
                    if assessment.invalid_reason is not None or assessment.max_violation > feasibility_tolerance:
                        continue
                    saving = current_mass - self._weighted_mass(assessment)
                    if saving <= 1e-12:
                        continue
                    move = (saving, element_id, ply_id, candidate, assessment)
                    if best_move is None:
                        best_move = move
                    elif (saving, -element_id, ply_id) > (
                        best_move[0], -best_move[1], best_move[2]
                    ):
                        best_move = move
                if not complete:
                    break
            if not complete or best_move is None:
                break
            _, element_id, ply_id, current_laminates, current_assessment = best_move
            removed.append((element_id, ply_id))
        return replace(
            current_assessment,
            extent_search_complete=complete,
            extent_removals=tuple(removed),
            extent_evaluations=evaluations,
        )
