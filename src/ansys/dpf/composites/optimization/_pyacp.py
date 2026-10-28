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

"""Optional guarded write-back to PyACP without a hard PyACP dependency."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose
from typing import Any, Literal

from ._problem import LaminateOptimizationResult


@dataclass(frozen=True)
class ACPAdditionTemplate:
    """Manufacturing extent for a new ply, inherited by cloning a modeling ply.

    The template must generate one nominal-thickness analysis ply. The local
    CLT angle equals the ACP design angle plus ``angle_offset``; draping changes
    are not predicted. Templates are keyed by added ply ID.
    """

    modeling_ply: Any
    angle_offset: float = 0.0


@dataclass(frozen=True)
class ACPChange:
    """Preflighted operation for one editable modeling ply."""

    ply_id: str
    operation: Literal["edit", "add", "deactivate"]
    angle: float | None = None
    material: str | None = None
    global_ply_number: int | None = None


class PyACPAdapter:
    """Apply a feasible result to explicitly bound one-to-one modeling plies.

    Construct before optimization to detect subsequent ACP changes. ``bindings``
    maps original analysis-ply IDs to ACP ModelingPly objects. Split repeated
    layers, stackups, variable thickness and ambiguous mappings first.

    ``fabrics`` maps optimization material names to ACP fabrics. New plies need
    manufacturing templates and explicit final ``global_order`` numbers, as
    does reordering. Choose numbers that avoid unsampled plies. Removals
    deactivate rather than delete modeling plies. Application defaults to dry
    run; save a backup before real application (there is no atomic rollback).

    Offsets are not edited. Changed offsets need ``offsets_verified=True`` to
    confirm the caller arranged matching ACP behavior. Always regenerate and
    verify the final ACP layups, including effects beyond the sampled points.
    """

    def __init__(
        self,
        model: Any,
        bindings: Mapping[str, Any],
        *,
        fabrics: Mapping[str, Any] | None = None,
    ) -> None:
        self.model = model
        self.bindings = dict(bindings)
        self.fabrics = dict(fabrics or {})
        identities = [getattr(p, "access_path", id(p)) for p in self.bindings.values()]
        if len(set(identities)) != len(identities):
            raise ValueError("Multiple analysis plies cannot bind to the same modeling ply.")
        self._snapshots = {key: self._state(ply) for key, ply in self.bindings.items()}

    @staticmethod
    def _state(ply: Any) -> tuple[Any, ...]:
        if ply.number_of_layers != 1 or str(ply.thickness_type) not in (
            "nominal",
            "ThicknessType.NOMINAL",
        ):
            raise ValueError(
                "PyACP write-back requires one nominal-thickness analysis ply per binding."
            )
        if not hasattr(ply.ply_material, "material") or not hasattr(ply.ply_material, "thickness"):
            raise ValueError("PyACP write-back requires a fabric, not a stackup or sublaminate.")
        production_plies = getattr(ply, "production_plies", None)
        if production_plies is not None:
            children = list(production_plies.values())
            if len(children) != 1 or len(children[0].analysis_plies) != 1:
                raise ValueError("The modeling ply does not generate exactly one analysis ply.")
        fabric = ply.ply_material
        return (
            ply.ply_angle,
            getattr(fabric, "access_path", id(fabric)),
            fabric.thickness,
            ply.global_ply_nr,
            ply.active,
        )

    def apply(
        self,
        result: LaminateOptimizationResult,
        *,
        dry_run: bool = True,
        addition_templates: Mapping[str, ACPAdditionTemplate] | None = None,
        global_order: Mapping[str, int] | None = None,
        offsets_verified: bool = False,
    ) -> tuple[ACPChange, ...]:
        """Preflight every operation, then optionally modify ACP and update once."""
        if not result.feasible:
            raise ValueError("Cannot apply an infeasible optimization result.")
        templates = dict(addition_templates or {})
        order = dict(global_order or {})
        for key, ply in self.bindings.items():
            if self._state(ply) != self._snapshots[key]:
                raise ValueError(f"ACP binding {key!r} changed since the adapter was created.")
        initial, optimized = result.changes.initial, result.changes.optimized
        if not offsets_verified and any(
            not isclose(a.offset, b.offset, rel_tol=0, abs_tol=1e-12)
            for a, b in zip(initial, optimized)
        ):
            raise ValueError(
                "Changed offsets require explicit verification of ACP offset behavior."
            )
        topology_changed = False
        for a, b in zip(initial, optimized):
            old_ids, new_ids = [p.id for p in a.plies], [p.id for p in b.plies]
            surviving = set(old_ids) & set(new_ids)
            if [p for p in old_ids if p in surviving] != [p for p in new_ids if p in surviving]:
                topology_changed = True
            if set(new_ids) - set(old_ids):
                topology_changed = True
        if topology_changed and not order:
            raise ValueError(
                "Additions and reordering require explicit final global_order numbers."
            )
        if order:
            if len(set(order.values())) != len(order) or any(
                not isinstance(n, int) or isinstance(n, bool) for n in order.values()
            ):
                raise ValueError("global_order numbers must be unique integers.")
            for point in optimized:
                if any(p.id not in order for p in point.plies):
                    raise ValueError("global_order must cover every final local ply.")
                numbers = [order[p.id] for p in point.plies]
                if numbers != sorted(numbers):
                    raise ValueError("global_order contradicts a final local stack.")
        changes_by_id: dict[str, list[Any]] = {}
        for change in result.changes.changes:
            changes_by_id.setdefault(change.ply_id, []).append(change)
        for key in order:
            changes_by_id.setdefault(key, [])
        actions = []
        target_fabrics: dict[str, Any] = {}
        for key, changes in changes_by_id.items():
            if not changes:
                if key not in self.bindings:
                    raise ValueError(f"Missing modeling-ply binding for {key!r}.")
                actions.append(ACPChange(key, "edit", global_ply_number=order.get(key)))
                continue
            first = changes[0]
            operation: Literal["edit", "add", "deactivate"]
            if first.before is not None and key not in self.bindings:
                raise ValueError(f"Missing modeling-ply binding for {key!r}.")
            if first.after is None:
                if any(c.after is not None for c in changes):
                    raise ValueError("A shared ply cannot be removed at only some points.")
                actions.append(ACPChange(key, "deactivate"))
                continue
            if first.before is None:
                if key not in templates:
                    raise ValueError(f"Addition {key!r} needs an explicit manufacturing template.")
                self._state(templates[key].modeling_ply)
                angle = first.after.angle - templates[key].angle_offset
                if any(c.after != first.after for c in changes):
                    raise ValueError(
                        "New plies with different local properties need a custom adapter."
                    )
                operation = "add"
            else:
                deltas = [c.after.angle - c.before.angle for c in changes]
                if any(not isclose(d, deltas[0], abs_tol=1e-8) for d in deltas):
                    raise ValueError("Local angle edits do not map to one ACP design-angle change.")
                angle = self.bindings[key].ply_angle + deltas[0]
                operation = "edit"
            after = first.after
            if any(
                c.after.material_name != after.material_name
                or not isclose(c.after.thickness, after.thickness, rel_tol=1e-8)
                for c in changes
            ):
                raise ValueError("Local material/thickness edits need a custom ACP adapter.")
            fabric = self.fabrics.get(after.material_name)
            if (
                fabric is None
                and operation == "edit"
                and all(
                    c.before.material_name == c.after.material_name
                    and c.before.thickness == c.after.thickness
                    for c in changes
                )
            ):
                fabric = self.bindings[key].ply_material
            if fabric is None or not isclose(fabric.thickness, after.thickness, rel_tol=1e-8):
                raise ValueError(
                    f"Material {after.material_name!r} needs a fabric with matching thickness."
                )
            target_fabrics[key] = fabric
            actions.append(ACPChange(key, operation, angle, after.material_name, order.get(key)))
        if not dry_run:
            for action in actions:
                if action.operation == "add":
                    source = templates[action.ply_id].modeling_ply
                    ply = source.clone()
                    ply.name = action.ply_id.replace(":", "_")
                    ply.ply_angle = action.angle
                    ply.ply_material = target_fabrics[action.ply_id]
                    ply.global_ply_nr = action.global_ply_number
                    ply.active = True
                    ply.store(source.parent)
                    self.bindings[action.ply_id] = ply
                else:
                    ply = self.bindings[action.ply_id]
                    if action.operation == "deactivate":
                        ply.active = False
                    else:
                        if action.angle is not None:
                            ply.ply_angle = action.angle
                            ply.ply_material = target_fabrics[action.ply_id]
                        if action.global_ply_number is not None:
                            ply.global_ply_nr = action.global_ply_number
            self.model.update()
        return tuple(actions)
