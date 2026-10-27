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

"""Integration with the standalone CLT operator on an explicitly supplied server."""

from dataclasses import replace

from ansys.dpf.core import Operator
import pytest

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.optimization import (
    ClassicalLaminateEvaluator,
    Laminate,
    LaminateForces,
    LoadCase,
)

from .helper import get_dummy_data_files
from .optimization_test import in_plane_criterion


def test_clt_mass_and_multiple_load_cases(dpf_server):
    try:
        Operator("composite::classical_laminate_theory_operator", server=dpf_server)
    except KeyError:
        pytest.skip("Loaded plugin does not provide standalone CLT (capability, not version).")
    criterion = in_plane_criterion()
    model = CompositeModel(get_dummy_data_files(False), server=dpf_server)
    sample = model.get_sampling_point(criterion, element_id=1)
    if "materials" not in sample.results[0]:
        pytest.skip("Loaded plugin does not export sampling point material definitions for CLT.")
    # Explicit cases also exercise optimization independently of original loads.
    cases = (
        LoadCase("one", LaminateForces(Nx=100)),
        LoadCase("two", LaminateForces(Nx=200)),
    )
    point = Laminate.from_sampling_point(sample, load_cases=cases)
    materials = {m.name: m for m in point.materials}
    plies = tuple(p for p in point.plies if materials[p.material].ply_type in ("regular", "woven"))
    # This test evaluates a fiber-only CLT laminate, not the core's unsupported
    # max-stress failure. The original sample itself is never modified.
    point = replace(point, plies=plies, offset=-sum(p.thickness for p in plies) / 2)
    evaluator = ClassicalLaminateEvaluator(model.material_operators.material_provider, criterion)
    first, second = (evaluator(point, case) for case in cases)
    assert first.mass_per_unit_area > 0
    assert first.mass_per_unit_area == pytest.approx(second.mass_per_unit_area)
    assert second.max_irf == pytest.approx(2 * first.max_irf)
    assert first.max_irf > 0
