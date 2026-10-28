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

"""Cached multi-point/multi-case optimization and explicit result change sets."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from math import inf, isfinite
from typing import Any, Protocol

from ..layup_info import AnalysisPlyInfo
from ._design_space import InvalidDesign, LaminateDesignSpace
from ._evaluator import LaminateEvaluator
from ._models import Laminate, LaminateResponse, _finite


@dataclass(frozen=True)
class PointResult:
    """Named point and load case with a CLT response."""

    point: str
    load_case: str
    response: LaminateResponse


@dataclass(frozen=True)
class CandidateEvaluation:
    """Objective and fixed-size constraints, feasible when each is <= tolerance."""

    values: tuple[float, ...]
    laminates: tuple[Laminate, ...]
    results: tuple[PointResult, ...]
    objective: float
    constraints: tuple[float, ...]
    invalid_reason: str | None = None
    extent_search_complete: bool = True
    extent_removals: tuple[tuple[int, str], ...] = ()
    extent_evaluations: int = 0

    @property
    def max_violation(self) -> float:
        """Maximum positive constraint violation."""
        return max((0.0, *self.constraints))


@dataclass(frozen=True)
class PlyChange:
    """One local edit, addition or removal, identified by analysis-ply ID."""

    point: str
    ply_id: str
    before: AnalysisPlyInfo | None
    after: AnalysisPlyInfo | None


@dataclass(frozen=True)
class LaminateChangeSet:
    """Full before/after snapshots and ID-based edits for external model adapters.

    Snapshots retain final ordering and changes outside the common editable
    subset. Added IDs start with ``added:`` and need a manufacturing extent.
    """

    initial: tuple[Laminate, ...]
    optimized: tuple[Laminate, ...]
    changes: tuple[PlyChange, ...]

    @classmethod
    def between(
        cls, initial: Sequence[Laminate], optimized: Sequence[Laminate]
    ) -> LaminateChangeSet:
        """Compare local stacks by stable IDs, not array positions."""
        if [p.name for p in initial] != [p.name for p in optimized]:
            raise ValueError("Initial and optimized sampling point identities must match.")
        changes = []
        for before, after in zip(initial, optimized):
            old = {p.id: p for p in before.plies}
            new = {p.id: p for p in after.plies}
            for ply_id in dict.fromkeys((*old, *new)):
                if old.get(ply_id) != new.get(ply_id):
                    changes.append(PlyChange(before.name, ply_id, old.get(ply_id), new.get(ply_id)))
        return cls(tuple(initial), tuple(optimized), tuple(changes))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable change set, including complete final orders."""

        def snapshot(point: Laminate) -> dict[str, Any]:
            return {
                "name": point.name,
                "unit_system": point.unit_system,
                "offset": point.offset,
                "plies": [asdict(p) for p in point.plies],
            }

        return {
            "initial": [snapshot(p) for p in self.initial],
            "optimized": [snapshot(p) for p in self.optimized],
            "changes": [asdict(c) for c in self.changes],
        }


@dataclass(frozen=True)
class LaminateOptimizationResult:
    """Verified best candidate, separate from the solver's termination status."""

    best: CandidateEvaluation
    initial: CandidateEvaluation
    feasible: bool
    solver_success: bool
    message: str
    changes: LaminateChangeSet
    evaluations: tuple[CandidateEvaluation, ...]
    solver_result: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Export a compact report and the change set for PyACP or other clients."""
        return {
            "feasible": self.feasible,
            "solver_success": self.solver_success,
            "message": self.message,
            "objective": self.best.objective,
            "initial_objective": self.initial.objective,
            "constraints": list(self.best.constraints),
            "values": list(self.best.values),
            "extent_search_complete": self.best.extent_search_complete,
            "extent_removals": [list(removal) for removal in self.best.extent_removals],
            "extent_evaluations": self.best.extent_evaluations,
            "changes": self.changes.to_dict(),
            "results": [
                {
                    "point": p.point,
                    "load_case": p.load_case,
                    "mass_per_unit_area": p.response.mass_per_unit_area,
                    "inverse_reserve_factors": list(p.response.inverse_reserve_factors),
                    "failure_modes": list(p.response.failure_modes),
                }
                for p in self.best.results
            ],
        }


Metric = Callable[[tuple[Laminate, ...], tuple[PointResult, ...]], float]


class ExtentOptimizerProtocol(Protocol):
    """Structural protocol for an optional inner local ply-mask optimizer."""

    def optimize(
        self,
        laminates: tuple[Laminate, ...],
        assess: Callable[[tuple[Laminate, ...]], CandidateEvaluation],
        *,
        feasibility_tolerance: float = 1e-8,
    ) -> CandidateEvaluation:
        """Return the best feasible candidate after optimizing local ply extents."""
        raise NotImplementedError


class LaminateOptimizationProblem:
    """Optimize weighted mass subject to IRF limits at every point and load case.

    ``evaluator`` is any callable implementing LaminateEvaluator. Additional
    scalar constraints use the convention g <= 0; the default objective is the
    weighted mean mass per area, counted once per point, not once per load case.
    An IRF limit mapping must contain exactly the (point, case) keys.
    """

    def __init__(
        self,
        design_space: LaminateDesignSpace,
        evaluator: LaminateEvaluator,
        *,
        irf_limit: float | Mapping[tuple[str, str], float] = 1.0,
        objective: Metric | None = None,
        constraints: Sequence[Metric] = (),
        feasibility_tolerance: float = 1e-8,
        extent_optimizer: ExtentOptimizerProtocol | None = None,
    ) -> None:
        self.design_space = design_space
        self.evaluator = evaluator
        self._objective = objective
        self._constraints = tuple(constraints)
        self.extent_optimizer = extent_optimizer
        _finite(feasibility_tolerance, "feasibility_tolerance")
        if feasibility_tolerance < 0:
            raise ValueError("feasibility_tolerance must be nonnegative.")
        self.feasibility_tolerance = feasibility_tolerance
        self.case_keys = tuple(
            (p.name, c.name) for p in design_space.laminates for c in p.load_cases
        )
        if isinstance(irf_limit, Mapping):
            if set(irf_limit) != set(self.case_keys):
                raise ValueError("IRF limits must contain exactly the (point, load-case) keys.")
            self._limits = tuple(irf_limit[k] for k in self.case_keys)
        else:
            self._limits = (irf_limit,) * len(self.case_keys)
        for limit in self._limits:
            _finite(limit, "irf_limit", positive=True)
        self._cache: dict[tuple[float, ...], CandidateEvaluation] = {}
        self._history: list[CandidateEvaluation] = []

    @property
    def evaluations(self) -> tuple[CandidateEvaluation, ...]:
        """Actual evaluations (cache hits are not duplicated)."""
        return tuple(self._history)

    def evaluate(self, values: Sequence[float], *, use_cache: bool = True) -> CandidateEvaluation:
        """Evaluate a candidate; backend errors are not hidden as infeasibility."""
        key = tuple(float(v) for v in values)
        if use_cache and key in self._cache:
            return self._cache[key]
        try:
            laminates = self.design_space.decode(key)
        except InvalidDesign as error:
            evaluation = CandidateEvaluation(
                key,
                (),
                (),
                inf,
                (inf,) * (len(self.case_keys) + len(self._constraints)),
                str(error),
            )
        else:
            def assess(candidate_laminates: tuple[Laminate, ...]) -> CandidateEvaluation:
                results = tuple(
                    PointResult(point.name, case.name, self.evaluator(point, case))
                    for point in candidate_laminates
                    for case in point.load_cases
                )
                masses: dict[str, float] = {}
                for point_result in results:
                    response = point_result.response
                    point = next(p for p in candidate_laminates if p.name == point_result.point)
                    if len(response.inverse_reserve_factors) != len(point.plies):
                        raise ValueError("Evaluator must return one IRF per ply.")
                    if point.name in masses and abs(
                        masses[point.name] - response.mass_per_unit_area
                    ) > (1e-8 * max(masses[point.name], response.mass_per_unit_area)):
                        raise ValueError(
                            "Evaluator returned load-dependent mass for the same laminate."
                        )
                    masses[point.name] = response.mass_per_unit_area
                objective = (
                    self._objective(candidate_laminates, results)
                    if self._objective
                    else sum(p.weight * masses[p.name] for p in candidate_laminates)
                    / sum(p.weight for p in candidate_laminates)
                )
                constraints = tuple(
                    result.response.max_irf - limit
                    for result, limit in zip(results, self._limits)
                ) + tuple(metric(candidate_laminates, results) for metric in self._constraints)
                if not isfinite(objective) or not all(isfinite(v) for v in constraints):
                    raise ValueError("Objective and constraint callbacks must return finite values.")
                return CandidateEvaluation(
                    key, candidate_laminates, results, float(objective), constraints
                )

            evaluation = (
                self.extent_optimizer.optimize(
                    laminates, assess, feasibility_tolerance=self.feasibility_tolerance
                )
                if self.extent_optimizer is not None
                else assess(laminates)
            )
        self._cache[key] = evaluation
        self._history.append(evaluation)
        return evaluation

    def objective(self, values: Sequence[float]) -> float:
        """Scalar solver objective; shares the evaluation cache with constraints."""
        return self.evaluate(values).objective

    def constraint_values(self, values: Sequence[float]) -> tuple[float, ...]:
        """Fixed-size vector with g <= 0 convention."""
        return self.evaluate(values).constraints

    def optimize(self, optimizer: Callable[..., Any], **options: Any) -> LaminateOptimizationResult:
        """Call ``optimizer(problem, **options)`` and verify its best feasible design.

        The callable returns a SciPy-like result with ``x``, ``success`` and
        ``message`` attributes (or mapping keys). Previously cached evaluations
        are reused. Both the best feasible point and an infeasible fallback are
        re-evaluated without cache before reporting. Success never guarantees a
        global optimum or FE-level structural feasibility.
        """
        initial = self.evaluate(self.design_space.initial)
        if self.design_space.variables:
            raw = optimizer(self, **options)
            get = (
                raw.get
                if isinstance(raw, Mapping)
                else lambda key, default=None: getattr(raw, key, default)
            )
            values = get("x")
            if values is None:
                raise ValueError("Optimizer result must provide a numerical candidate 'x'.")
            self.evaluate(values)
            success = bool(get("success", False))
            message = str(get("message", ""))
        else:
            raw, success, message = None, True, "No free design variables."
        valid = [v for v in self._cache.values() if v.invalid_reason is None]
        if not valid:
            raise InvalidDesign("No structurally valid laminate was evaluated.")
        feasible = [v for v in valid if v.max_violation <= self.feasibility_tolerance]
        best = (
            min(feasible, key=lambda v: v.objective)
            if feasible
            else min(valid, key=lambda v: (v.max_violation, v.objective))
        )
        best = self.evaluate(best.values, use_cache=False)
        return LaminateOptimizationResult(
            best,
            initial,
            best.max_violation <= self.feasibility_tolerance,
            success,
            message,
            LaminateChangeSet.between(self.design_space.laminates, best.laminates),
            self.evaluations,
            raw,
        )
