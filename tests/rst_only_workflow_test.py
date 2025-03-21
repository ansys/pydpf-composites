# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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

import numpy.testing
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    FaceSheetWrinklingCriterion,
    HashinCriterion,
    MaxStressCriterion,
    ShearCrimpingCriterion,
)
from ansys.dpf.composites.layup_info import (
    LayerProperty,
    LayupModelContextType,
    get_analysis_ply_index_to_name_map,
)
from ansys.dpf.composites.layup_info.material_properties import MaterialProperty
from ansys.dpf.composites.server_helpers import version_equal_or_later, version_older_than

from .helper import Timer

SEPARATOR = "::"


def test_composite_model_with_rst_only(dpf_server, data_files, distributed_rst):
    """Test features of the composite model with section data from the RST file only."""
    if version_older_than(dpf_server, "8.0"):
        pytest.xfail("Section data from RST is supported since server version 8.0 (2024 R2).")

    timer = Timer()

    # remove composite definitions from ContinuousFiberCompositesFiles so that the section
    # data is loaded from the RST
    data_files.composite = {}

    composite_model = CompositeModel(data_files, server=dpf_server)
    assert composite_model.layup_model_type == LayupModelContextType.RST

    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max stress",
        failure_criteria=[
            MaxStressCriterion(),
            HashinCriterion(hd=True, dim=3),
            CoreFailureCriterion(),
            FaceSheetWrinklingCriterion(),
            ShearCrimpingCriterion(),
        ],
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criterion=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )
    irf_field = failure_output.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    fm_field = failure_output.get_field({"failure_label": FailureOutput.FAILURE_MODE})

    property_dict = composite_model.get_constant_property_dict([MaterialProperty.Stress_Limits_Xt])

    timer.add("After get property dict")

    element_infos = [
        composite_model.get_element_info(element_id)
        for element_id in composite_model.get_mesh().elements.scoping.ids
    ]
    get_analysis_ply_index_to_name_map(composite_model.get_mesh())

    timer.add("After getting element_info")

    expected_values = {
        LayerProperty.ANGLES: [45, 0, 0, 0, 0, 45],
        LayerProperty.THICKNESSES: [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025],
    }
    element_id = 1
    for layer_property, value in expected_values.items():
        numpy.testing.assert_allclose(
            composite_model.get_property_for_all_layers(layer_property, element_id), value
        )

    # shear angles, analysis plies and offset are not available in the RST file
    assert (
        composite_model.get_property_for_all_layers(LayerProperty.SHEAR_ANGLES, element_id) is None
    )
    assert composite_model.get_element_laminate_offset(element_id) is None
    assert composite_model.get_analysis_plies(element_id) is None

    assert composite_model.core_model is not None
    assert composite_model.get_mesh() is not None
    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion, element_id=1
    )

    assert [ply["thickness"] for ply in sampling_point.analysis_plies] == expected_values[
        LayerProperty.THICKNESSES
    ]

    if version_equal_or_later(dpf_server, "7.1"):
        ref_material_names = [
            "Epoxy Carbon UD (230 GPa) Prepreg",
            "Epoxy Carbon Woven (230 GPa) Wet",
            "Honeycomb",
            "Structural Steel",
        ]
        mat_names = composite_model.material_names
        assert len(mat_names) == len(ref_material_names)
        for mat_name in ref_material_names:
            assert mat_name in mat_names.keys()

    timer.add("After getting properties")

    timer.summary()
