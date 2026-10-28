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

"""DPF-backed classical laminate theory evaluation."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any, Protocol

from ansys.dpf.core import Operator, types

from ._models import Laminate, LaminateResponse, LoadCase


class LaminateEvaluator(Protocol):
    """Evaluation interface; custom implementations are useful for testing."""

    def __call__(self, laminate: Laminate, load_case: LoadCase) -> LaminateResponse:
        """Evaluate one complete local laminate under fixed resultants."""


class ClassicalLaminateEvaluator:
    """Evaluate mass and in-plane failures using the standalone DPF CLT operator.

    Parameters
    ----------
    materials_provider:
        Operator whose first output is a materials container, for example
        ``composite_model.material_operators.material_provider``. Every candidate
        material external ID must be present, including replacement materials.
    failure_criteria:
        CombinedFailureCriterion, its JSON string, or the equivalent dictionary.
        Only CLT-compatible in-plane criteria are supported. Variable materials
        are evaluated at their default state by the backend.

    Notes
    -----
    Keep a DPF LicenseContextManager for ``acpreppost`` around an optimization
    run to avoid repeated checkout overhead. Evaluation is serial; this object
    does not promise thread safety. Backend errors are deliberately propagated.
    """

    def __init__(self, materials_provider: Operator, failure_criteria: Any) -> None:
        self.materials_provider = materials_provider
        if hasattr(failure_criteria, "to_json"):
            failure_criteria = failure_criteria.to_json()
        if isinstance(failure_criteria, str):
            failure_criteria = json.loads(failure_criteria)
        if not isinstance(failure_criteria, Mapping):
            raise TypeError("failure_criteria must be a criterion, JSON string or mapping.")
        if "failure_criteria_definition" not in failure_criteria:
            failure_criteria = {
                "version": 1,
                "accumulator": "max",
                "expression": "composite_failure",
                "failure_criteria_definition": {"criteria": failure_criteria},
            }
        try:
            criteria = failure_criteria["failure_criteria_definition"]["criteria"]
        except KeyError as error:
            raise ValueError("Expected a combined failure criteria definition.") from error
        self._criteria = {name: config for name, config in criteria.items() if config.get("active")}
        if not self._criteria:
            raise ValueError("At least one failure criterion must be active.")
        supported = {
            "max_stress",
            "max_strain",
            "von_mises",
            "hashin",
            "puck",
            "larc",
            "cuntze",
            "tsai_hill",
            "tsai_wu",
            "hoffman",
            "face_sheet_wrinkling",
            "shear_crimping",
        }
        if self._criteria.keys() - supported:
            raise ValueError("The criteria include a failure mode unsupported by standalone CLT.")
        for name, config in self._criteria.items():
            if name in ("max_stress", "max_strain"):
                components = ("s3", "s13", "s23") if name == "max_stress" else ("e3", "e13", "e23")
                if any(config.get(c) for c in components):
                    raise ValueError(f"CLT {name} cannot use out-of-plane components.")
                in_plane = ("s1", "s2", "s12") if name == "max_stress" else ("e1", "e2", "e12")
                if not any(config.get(c) for c in in_plane):
                    raise ValueError(f"CLT {name} requires an active in-plane component.")
            elif name == "von_mises":
                if config.get("eval_ins") or not (config.get("vme") or config.get("vms")):
                    raise ValueError("CLT von_mises requires an in-plane stress or strain check.")
            elif name in ("hashin", "puck", "larc", "cuntze", "tsai_hill", "tsai_wu", "hoffman"):
                if config.get("dim") != 2:
                    raise ValueError(f"CLT requires the two-dimensional {name} criterion.")
        self._failure_json = json.dumps(failure_criteria, allow_nan=False)

    def _check_coverage(self, laminate: Laminate) -> None:
        active = set(self._criteria)
        general = {"max_stress", "max_strain", "tsai_hill", "tsai_wu", "hoffman"}
        unidirectional = general | {"hashin", "puck", "larc", "cuntze"}
        catalog = {m.name: m for m in laminate.materials}
        for ply in laminate.plies:
            material = catalog[ply.material_name]
            covered = (
                (material.ply_type == "regular" and bool(active & unidirectional))
                or (material.ply_type == "woven" and bool(active & general))
                or (material.ply_type == "isotropic" and "von_mises" in active)
                or (material.is_core and "shear_crimping" in active)
            )
            if not covered:
                raise ValueError(
                    f"Ply {ply.id!r} ({material.ply_type}) has no applicable CLT failure criterion."
                )

    def __call__(self, laminate: Laminate, load_case: LoadCase) -> LaminateResponse:
        self._check_coverage(laminate)
        try:
            operator = Operator(
                "composite::classical_laminate_theory_operator",
                server=self.materials_provider._server,
            )
        except KeyError as error:
            raise RuntimeError(
                "The loaded DPF Composites plugin does not provide the standalone "
                "classical laminate theory operator. Load a CLT-capable plugin build."
            ) from error
        operator.inputs.layup_definition(
            json.dumps(laminate.to_clt_dict(load_case), allow_nan=False)
        )
        operator.inputs.materials_container(self.materials_provider.outputs)
        operator.inputs.failure_criteria_definition(self._failure_json)
        operator.inputs.compute_mass_per_area(True)
        operator.inputs.compute_laminate_properties(False)
        operator.inputs.compute_strains_and_stresses(True)
        document = json.loads(operator.get_output(0, types.string))
        failures = document["results"]["failures"]
        irfs = tuple(float(v) for v in failures["inverse_reserve_factor"])
        if len(irfs) != len(laminate.plies):
            raise RuntimeError("CLT returned an unexpected number of ply failure results.")
        return LaminateResponse(
            float(document["mass_per_unit_area"]),
            irfs,
            tuple(failures["failure_modes"]),
            document,
        )
