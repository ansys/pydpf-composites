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

"""Mixed-variable candidate decoding with structural laminate symmetry."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from math import isclose, isfinite
from typing import Literal

from ..layup_info import AnalysisPlyInfo
from ._models import Laminate, Material, _finite


class InvalidDesign(ValueError):
    """A candidate violates a structural constraint (not a backend failure)."""


@dataclass(frozen=True)
class AngleBounds:
    """Continuous angle domain in degrees."""

    lower: float
    upper: float

    def __post_init__(self) -> None:
        _finite(self.lower, "lower angle")
        _finite(self.upper, "upper angle")
        if self.lower > self.upper:
            raise ValueError("Angle lower bound exceeds upper bound.")


@dataclass(frozen=True)
class DiscreteAngles:
    """Exact allowed angles in degrees; encoded as integer indices."""

    values: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))
        if not self.values or len(set(self.values)) != len(self.values):
            raise ValueError("Discrete angles must be nonempty and unique.")
        for value in self.values:
            _finite(value, "angle")


@dataclass(frozen=True)
class PlyRule:
    """Allowed edits to a shared ply; unspecified attributes remain fixed.

    ``angle_mode='offset'`` applies a common change to the original local angle
    at each point; ``'absolute'`` assigns the same local angle everywhere.
    Material eligibility is fixed by this rule, never by a replacement chain.
    """

    angles: AngleBounds | DiscreteAngles | None = None
    materials: tuple[str, ...] = ()
    removable: bool = False
    angle_mode: Literal["absolute", "offset"] = "absolute"
    use_material_thickness: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "materials", tuple(self.materials))
        if self.angles is not None and not isinstance(self.angles, (AngleBounds, DiscreteAngles)):
            raise TypeError("angles must be AngleBounds, DiscreteAngles or None.")
        if self.angle_mode not in ("absolute", "offset"):
            raise ValueError("angle_mode must be 'absolute' or 'offset'.")
        if len(set(self.materials)) != len(self.materials):
            raise ValueError("Replacement materials must be unique.")


@dataclass(frozen=True)
class AdditionRule:
    """Bounded optional additions, all propagated to every sampling point.

    Each slot selects an insertion gap in the design space's global ply order.
    The optimizer chooses that gap; the user need not anchor it to an existing
    ply. With symmetry, each slot creates a mirrored pair of equal plies.
    """

    name: str
    materials: tuple[str, ...]
    thickness: float
    angles: AngleBounds | DiscreteAngles = DiscreteAngles((0.0,))
    max_count: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "materials", tuple(self.materials))
        if not self.name or ":" in self.name or not self.materials:
            raise ValueError("Addition needs a nonempty colon-free name and materials.")
        if not isinstance(self.angles, (AngleBounds, DiscreteAngles)):
            raise TypeError("Addition angles must be AngleBounds or DiscreteAngles.")
        if len(set(self.materials)) != len(self.materials):
            raise ValueError("Addition materials must be unique.")
        if isinstance(self.max_count, bool) or not isinstance(self.max_count, int):
            raise ValueError("max_count must be an integer.")
        if self.max_count < 1:
            raise ValueError("max_count must be positive.")
        _finite(self.thickness, "addition thickness", positive=True)


@dataclass(frozen=True)
class DesignVariable:
    """One numerical solver variable and its domain."""

    name: str
    lower: float
    upper: float
    initial: float
    integer: bool = False


class LaminateDesignSpace:
    """Compile common ply edits into a fixed-dimensional numerical design.

    Symmetry requires initially symmetric complete local stacks. Mirrored ply
    IDs are linked across all points; their rules must agree. Existing odd
    center plies remain independent. Reordering currently requires identical
    complete ply-ID sequences across the points; fixed local patches otherwise
    remain untouched. Angles are symmetric modulo 180 degrees, not balanced.
    """

    def __init__(
        self,
        laminates: Sequence[Laminate],
        *,
        ply_rules: Mapping[str, PlyRule] | None = None,
        default_rule: PlyRule | None = None,
        additions: Sequence[AdditionRule] = (),
        materials: Sequence[Material] = (),
        symmetric: bool = False,
        allow_reordering: bool = False,
        minimum_plies: int = 1,
        offset_policy: Literal["bottom", "midplane"] = "midplane",
    ) -> None:
        self.laminates = tuple(laminates)
        if not self.laminates:
            raise ValueError("At least one laminate is required.")
        if len({p.name for p in self.laminates}) != len(self.laminates):
            raise ValueError("Sampling point names must be unique.")
        if len({p.unit_system for p in self.laminates}) != 1:
            raise ValueError("Normalize all sampling points to the same unit system first.")
        if offset_policy not in ("bottom", "midplane"):
            raise ValueError("offset_policy must be 'bottom' or 'midplane'.")
        if not isinstance(minimum_plies, int) or minimum_plies < 1:
            raise ValueError("minimum_plies must be a positive integer.")
        self.symmetric = symmetric
        self.allow_reordering = allow_reordering
        self.minimum_plies = minimum_plies
        self.offset_policy = offset_policy
        self.materials: dict[str, Material] = {}
        for material in [m for p in self.laminates for m in p.materials] + list(materials):
            if material.name in self.materials:
                previous = self.materials[material.name]
                if replace(previous, nominal_thickness=None) != replace(
                    material, nominal_thickness=None
                ):
                    raise ValueError(f"Conflicting definitions of material {material.name!r}.")
                if material.nominal_thickness is None:
                    continue
                if previous.nominal_thickness not in (None, material.nominal_thickness):
                    raise ValueError(f"Conflicting nominal thickness for {material.name!r}.")
            self.materials[material.name] = material
        self.additions = tuple(additions)
        if len({a.name for a in self.additions}) != len(self.additions):
            raise ValueError("Addition names must be unique.")
        existing_ids = {p.id for point in self.laminates for p in point.plies}
        if any(p.startswith("added:") for p in existing_ids):
            raise ValueError("The 'added:' ID prefix is reserved for new plies.")
        source_numbers: dict[str, int] = {}
        observed_ids: list[str] = []
        for point in self.laminates:
            for ply in point.plies:
                if ply.id not in observed_ids:
                    observed_ids.append(ply.id)
                if ply.global_ply_number is not None:
                    if ply.id in source_numbers and source_numbers[ply.id] != ply.global_ply_number:
                        raise ValueError(
                            f"Conflicting global_ply_number values for shared ply {ply.id!r}."
                        )
                    source_numbers[ply.id] = ply.global_ply_number
        if len(source_numbers) == len(observed_ids):
            self.global_ply_ids = tuple(
                sorted(
                    observed_ids,
                    key=lambda ply_id: (source_numbers[ply_id], observed_ids.index(ply_id)),
                )
            )
        else:
            # With manually constructed plies lacking source numbers, preserve
            # first-stack order and append IDs seen only in later points.
            self.global_ply_ids = tuple(observed_ids)
        global_ids = set(self.global_ply_ids)
        common = set.intersection(*({p.id for p in point.plies} for point in self.laminates))
        self.common_ply_ids = tuple(ply_id for ply_id in self.global_ply_ids if ply_id in common)
        rules = dict.fromkeys(self.global_ply_ids, default_rule) if default_rule else {}
        rules.update(ply_rules or {})
        if set(rules) - global_ids:
            raise ValueError("Ply rules must refer to IDs present in at least one sampling point.")
        self.ply_rules = rules
        if not common and not self.additions and not rules:
            raise ValueError("No common plies or global ply rules; add plies or define global rules.")
        self._global_ply_ranks = {ply_id: index for index, ply_id in enumerate(self.global_ply_ids)}
        for point in self.laminates:
            ranks = [self._global_ply_ranks[ply.id] for ply in point.plies]
            if ranks != sorted(ranks):
                raise ValueError(
                    f"Laminate {point.name!r} order conflicts with the global ply order."
                )
        self._addition_positions: dict[str, tuple[int, ...]] = {}
        for addition in self.additions:
            valid_gaps: list[int] = []
            for global_gap in range(len(self.global_ply_ids) + 1):
                local_gaps = [
                    self._project_global_gap(point.plies, global_gap) for point in self.laminates
                ]
                if not symmetric or all(
                    gap <= len(point.plies) // 2
                    for point, gap in zip(self.laminates, local_gaps)
                ):
                    valid_gaps.append(global_gap)
            if not valid_gaps:
                raise ValueError(f"Addition {addition.name!r} has no valid insertion gaps.")
            self._addition_positions[addition.name] = tuple(valid_gaps)
        # Reserve per-slot numbers once over the complete input set, not per
        # point or candidate. Inactive and removed plies never cause reuse.
        next_number = max(source_numbers.values(), default=0) + 1
        self._added_ply_numbers: dict[str, int] = {}
        for addition in self.additions:
            for slot in range(addition.max_count):
                key = f"added:{addition.name}:{slot}"
                self._added_ply_numbers[key] = next_number
                next_number += 1
                if symmetric:
                    self._added_ply_numbers[key + ":mirror"] = next_number
                    next_number += 1
        for point in self.laminates:
            if len(point.plies) < minimum_plies:
                raise ValueError("Initial laminate violates minimum_plies.")
        for rule in rules.values():
            self._check_materials(rule.materials)
            if rule.use_material_thickness:
                for name in rule.materials:
                    if self.materials[name].nominal_thickness is None:
                        raise ValueError(f"Replacement {name!r} needs a nominal thickness.")
        for addition in self.additions:
            self._check_materials(addition.materials)
        ids = tuple(p.id for p in self.laminates[0].plies)
        if allow_reordering and any(tuple(p.id for p in s.plies) != ids for s in self.laminates):
            raise ValueError("Reordering requires identical complete ply-ID sequences.")
        # Union reflected IDs so one decision affects every local mirror partner.
        parent = {p: p for p in self.global_ply_ids}

        def root(ply_id: str) -> str:
            while parent[ply_id] != ply_id:
                ply_id = parent[ply_id]
            return ply_id

        if symmetric:
            for point in self.laminates:
                if not point.is_symmetric():
                    raise ValueError(f"Initial laminate {point.name!r} is not symmetric.")
                for bottom, top in zip(point.plies, reversed(point.plies)):
                    if (bottom.id in rules) != (top.id in rules):
                        raise ValueError("A symmetric edit needs rules for both mirror plies.")
                    if bottom.id in rules:
                        if rules[bottom.id] != rules[top.id]:
                            raise ValueError("Mirrored plies must have identical edit rules.")
                    if bottom.id in global_ids and top.id in global_ids:
                        parent[root(top.id)] = root(bottom.id)
        self._groups: list[tuple[str, ...]] = []
        for ply_id in self.global_ply_ids:
            if not any(ply_id in group for group in self._groups):
                self._groups.append(
                    tuple(p for p in self.global_ply_ids if root(p) == root(ply_id))
                )
        # Reordering a shared group with several different mirror partners would
        # not define one global permutation. Reject it rather than guessing.
        if symmetric and allow_reordering and any(len(g) > 2 for g in self._groups):
            raise ValueError("Reordering requires consistent mirror pairs across sampling points.")
        self._variables: list[DesignVariable] = []
        self._indices: dict[tuple[str, str], int] = {}
        first = {p.id: p for point in self.laminates for p in point.plies}
        for rank, group in enumerate(self._groups):
            key = group[0]
            rule = rules.get(key, PlyRule())
            occurrences = [p for point in self.laminates for p in point.plies if p.id in group]
            if rule.angles is not None and rule.angle_mode == "absolute":
                if any(
                    abs((p.angle - first[key].angle + 90) % 180 - 90) > 1e-8 for p in occurrences
                ):
                    raise ValueError("Different local baseline angles require angle_mode='offset'.")
            if rule.materials and any(
                p.material_name != first[key].material_name for p in occurrences
            ):
                raise ValueError("A shared material variable requires one initial material.")
            if rule.use_material_thickness and rule.materials:
                nominal = self.materials[first[key].material_name].nominal_thickness
                if nominal is None or any(
                    not isclose(p.thickness, nominal, rel_tol=1e-8) for p in occurrences
                ):
                    raise ValueError(
                        "Initial ply thickness must match its nominal material thickness."
                    )
            if rule.removable:
                self._add(key, "active", 0, 1, 1, True)
            self._angle_variables(
                key, rule.angles, 0 if rule.angle_mode == "offset" else first[key].angle
            )
            if rule.materials:
                if any(first[p].material_name not in rule.materials for p in group):
                    raise ValueError("Replacement group must include each initial material.")
                self._add(
                    key,
                    "material",
                    0,
                    len(rule.materials) - 1,
                    rule.materials.index(first[key].material_name),
                    True,
                )
            if allow_reordering:
                self._add(key, "order", 0, max(len(self._groups) - 1, 1), rank, False)
        for addition in self.additions:
            for slot in range(addition.max_count):
                key = f"added:{addition.name}:{slot}"
                self._add(key, "active", 0, 1, 0, True)
                allowed_positions = self._addition_positions[addition.name]
                self._add(key, "position", 0, len(allowed_positions) - 1, 0, True)
                initial = (
                    addition.angles.values[0]
                    if isinstance(addition.angles, DiscreteAngles)
                    else addition.angles.lower
                )
                self._angle_variables(key, addition.angles, initial)
                self._add(key, "material", 0, len(addition.materials) - 1, 0, True)

    def _check_materials(self, names: Sequence[str]) -> None:
        if set(names) - set(self.materials):
            raise ValueError(f"Unknown material names: {set(names) - set(self.materials)}")

    def _project_global_gap(
        self,
        plies: Sequence[AnalysisPlyInfo],
        global_gap: int,
        candidate_order: Sequence[str] | None = None,
    ) -> int:
        """Map a global-order gap to a local stack, skipping absent/removed plies."""
        if candidate_order is not None:
            following_ids = set(candidate_order[global_gap:])
            for index, ply in enumerate(plies):
                if ply.id in following_ids:
                    return index
            return len(plies)
        for index, ply in enumerate(plies):
            if self._global_ply_ranks[ply.id] >= global_gap:
                return index
        return len(plies)

    def _add(
        self, key: str, kind: str, low: float, high: float, initial: float, integer: bool
    ) -> None:
        self._indices[key, kind] = len(self._variables)
        self._variables.append(DesignVariable(f"{key}.{kind}", low, high, initial, integer))

    def _angle_variables(
        self, key: str, domain: AngleBounds | DiscreteAngles | None, initial: float
    ) -> None:
        if isinstance(domain, DiscreteAngles):
            matches = [
                i
                for i, value in enumerate(domain.values)
                if abs((value - initial + 90) % 180 - 90) < 1e-8
            ]
            if matches:
                initial_index = matches[0]
            else:
                # The input layup need not use the requested candidate set.
                # Seed the search with the closest periodic allowed angle.
                initial_index = min(
                    range(len(domain.values)),
                    key=lambda index: (
                        abs((domain.values[index] - initial + 90) % 180 - 90),
                        abs(domain.values[index] - initial),
                    ),
                )
            self._add(key, "angle", 0, len(domain.values) - 1, initial_index, True)
        elif isinstance(domain, AngleBounds):
            if not domain.lower <= initial <= domain.upper:
                raise ValueError(f"Initial angle of {key!r} is outside its bounds.")
            self._add(key, "angle", domain.lower, domain.upper, initial, False)

    @property
    def variables(self) -> tuple[DesignVariable, ...]:
        """Solver variables in deterministic order."""
        return tuple(self._variables)

    @property
    def initial(self) -> tuple[float, ...]:
        """Initial numerical candidate (new ply slots are inactive)."""
        return tuple(v.initial for v in self._variables)

    @property
    def bounds(self) -> tuple[tuple[float, float], ...]:
        """Numerical bounds for solver adapters."""
        return tuple((v.lower, v.upper) for v in self._variables)

    @property
    def integrality(self) -> tuple[bool, ...]:
        """Mask for integer/categorical variables."""
        return tuple(v.integer for v in self._variables)

    def decode(self, values: Sequence[float]) -> tuple[Laminate, ...]:
        """Expand a numerical candidate to all complete local stacks."""
        if len(values) != len(self._variables):
            raise ValueError("Candidate size does not match the design space.")
        x = [float(v) for v in values]
        for index, (scalar, variable) in enumerate(zip(x, self._variables)):
            if not isfinite(scalar) or not variable.lower <= scalar <= variable.upper:
                raise ValueError(f"Candidate variable {variable.name!r} is outside its bounds.")
            if variable.integer:
                if not isclose(scalar, round(scalar), abs_tol=1e-8, rel_tol=0):
                    raise ValueError(f"Variable {variable.name!r} requires an integer index.")
                x[index] = float(round(scalar))

        def value(key: str, kind: str, default: float = 0) -> float:
            index = self._indices.get((key, kind))
            return default if index is None else x[index]

        def angle(key: str, domain: AngleBounds | DiscreteAngles) -> float:
            v = value(key, "angle")
            return domain.values[int(v)] if isinstance(domain, DiscreteAngles) else v

        decoded = []
        group_by_id = {p: g for g in self._groups for p in g}
        catalog = tuple(self.materials.values())
        for point in self.laminates:
            edited: dict[str, AnalysisPlyInfo] = {}
            for ply in point.plies:
                key = group_by_id[ply.id][0] if ply.id in group_by_id else ply.id
                rule = self.ply_rules.get(ply.id, PlyRule())
                if value(key, "active", 1) == 0:
                    continue
                new_angle = ply.angle
                if rule.angles is not None:
                    new_angle = angle(key, rule.angles)
                    if rule.angle_mode == "offset":
                        new_angle += ply.angle
                material = (
                    rule.materials[int(value(key, "material"))]
                    if rule.materials
                    else ply.material_name
                )
                thickness = ply.thickness
                if rule.use_material_thickness and rule.materials:
                    nominal = self.materials[material].nominal_thickness
                    assert nominal is not None
                    thickness = nominal
                edited[ply.id] = replace(
                    ply,
                    angle=new_angle,
                    material_name=material,
                    local_thickness=thickness,
                    nominal_thickness=(
                        self.materials[material].nominal_thickness
                        if material != ply.material_name
                        else ply.nominal_thickness
                    ),
                )
            ordered_ids = [p.id for p in point.plies]
            if self.allow_reordering:
                groups = sorted(self._groups, key=lambda g: value(g[0], "order"))
                if self.symmetric:
                    centers = [g[0] for g in groups if len(g) == 1]
                    bottoms = [g[0] for g in groups if len(g) == 2]
                    tops = [g[1] for g in reversed(groups) if len(g) == 2]
                    ordered_ids = bottoms + centers + tops
                else:
                    ordered_ids = [g[0] for g in groups]
            plies = [edited[p] for p in ordered_ids if p in edited]
            # Gaps are keyed by stable IDs; protected anchors survive removal.
            gaps: dict[int, list[AnalysisPlyInfo]] = {}
            mirror_gaps: dict[int, list[AnalysisPlyInfo]] = {}
            for addition in self.additions:
                for slot in range(addition.max_count):
                    key = f"added:{addition.name}:{slot}"
                    if value(key, "active") == 0:
                        continue
                    position_index = int(value(key, "position"))
                    global_gap = self._addition_positions[addition.name][position_index]
                    gap = self._project_global_gap(
                        plies,
                        global_gap,
                        ordered_ids if self.allow_reordering else None,
                    )
                    material = addition.materials[int(value(key, "material"))]
                    new_ply = AnalysisPlyInfo.from_local_ply(
                        id=key,
                        material_name=material,
                        angle=angle(key, addition.angles),
                        thickness=addition.thickness,
                        global_ply_number=self._added_ply_numbers[key],
                    )
                    gaps.setdefault(gap, []).append(new_ply)
                    if self.symmetric:
                        mirror_gaps.setdefault(len(plies) - gap, []).insert(
                            0,
                            replace(
                                new_ply,
                                id=key + ":mirror",
                                global_ply_number=self._added_ply_numbers[key + ":mirror"],
                            ),
                        )
            result: list[AnalysisPlyInfo] = []
            for i in range(len(plies) + 1):
                result.extend(gaps.get(i, ()))
                result.extend(mirror_gaps.get(i, ()))
                if i < len(plies):
                    result.append(plies[i])
            if len(result) < self.minimum_plies:
                raise InvalidDesign(f"Laminate {point.name!r} violates minimum_plies.")
            offset = point.offset
            if self.offset_policy == "midplane":
                offset += (point.thickness - sum(p.thickness for p in result)) / 2
            laminate = replace(point, plies=tuple(result), materials=catalog, offset=offset)
            if self.symmetric and not laminate.is_symmetric():
                raise InvalidDesign(f"Candidate laminate {point.name!r} is not symmetric.")
            decoded.append(laminate)
        return tuple(decoded)
