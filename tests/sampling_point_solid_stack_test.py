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
import json
import os
import pathlib

import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    FaceSheetWrinklingCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    PuckCriterion,
)
from ansys.dpf.composites.layup_info import SolidStackProvider
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.sampling_point_types import SamplingPoint, SamplingPointFigure
from ansys.dpf.composites.server_helpers import version_older_than

from .helper import compare_sampling_point_results

TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "solid_model"
ELEMENT_OF_CUTOFF_STACK = 219
ELEMENT_OF_DROPOFF_STACK = 154
ELEMENT_OF_LAYERED_STACK = 110


def get_file_paths() -> ContinuousFiberCompositesFiles:
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "file.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPSolidModel_SolidModel.1.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    files = ContinuousFiberCompositesFiles(
        result_files=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )
    return files


def get_fc() -> CombinedFailureCriterion:
    cfc = CombinedFailureCriterion("combined")
    cfc.insert(MaxStrainCriterion(e3=True, e13=True, e23=True))
    cfc.insert(MaxStressCriterion(s3=True, s13=True, s23=True))
    cfc.insert(PuckCriterion(pd=True, dim=3))
    cfc.insert(FaceSheetWrinklingCriterion())
    cfc.insert(CoreFailureCriterion(include_ins=True))
    return cfc


def compare_results(current, element_id, old) -> None:

    # Use this block to compare the entire output with a diff tool
    with open(os.path.join(TEST_DATA_ROOT_DIR, f"ref_{element_id}_current.txt"), "w") as f:
        json.dump(current, f, indent=4, sort_keys=True)

    suffix = "_old" if old else ""
    with open(os.path.join(TEST_DATA_ROOT_DIR, f"ref_{element_id}{suffix}.txt")) as f:
        reference = json.load(f)
    
    compare_sampling_point_results(current, reference, with_polar_properties=False)


def get_sampling_point_plot(sampling_point: SamplingPoint) -> SamplingPointFigure:
    return sampling_point.get_result_plots(
        strain_components=["e1", "e2", "e12"],
        stress_components=["s1", "s2", "s12"],
        failure_components=[FailureMeasureEnum.INVERSE_RESERVE_FACTOR],
        core_scale_factor=0.2,
        show_failure_modes=True,
    )


def test_solid_stack_layered_elements(dpf_server):
    """
    Test basic functionality
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Solid stack feature requires DPF server 10.0 or later.")
    composite_model = CompositeModel(get_file_paths(), server=dpf_server)
    solid_stack_provider = SolidStackProvider(
        composite_model.get_mesh(), composite_model.get_layup_operator()
    )

    assert solid_stack_provider.number_of_stacks == 34

    solid_stack = solid_stack_provider.get_solid_stack(ELEMENT_OF_LAYERED_STACK)
    assert solid_stack.number_of_elements == 5
    assert solid_stack.element_ids == [224, 60, 110, 143, 175]
    assert solid_stack.number_of_analysis_plies == 8
    assert solid_stack.element_wise_analysis_plies == {
        60: ["P1L1__woven up 45", "P1L1__woven up -45"],
        110: ["P1L1__Honeycomb up 5mm"],
        143: ["P1L1__ud up 0.2"],
        175: ["P1L1__woven up -45.2", "P1L1__woven up 45.2"],
        224: ["P1L1__woven down 45", "P1L1__woven down -45"],
    }
    assert solid_stack.element_wise_levels == {224: 0, 60: 1, 110: 2, 143: 3, 175: 4}
    ref_ply_thicknesses = {
        224: [0.0002499281471069403, 0.0002499281471069403],
        60: [0.00025000000000000017, 0.00025000000000000017],
        110: [0.004998642778686648],
        143: [0.0001999389250408988],
        175: [0.00025005356360532227, 0.00025005356360532227],
    }
    assert len(solid_stack.element_ply_thicknesses) == len(ref_ply_thicknesses)
    for element, thicknesses in solid_stack.element_ply_thicknesses.items():
        np.testing.assert_allclose(thicknesses, ref_ply_thicknesses[element], rtol=1e-6, atol=1e-8)

    assert solid_stack.element_ids_per_level == {0: [224], 1: [60], 2: [110], 3: [143], 4: [175]}
    solid_stacks = solid_stack_provider.get_solid_stacks(element_ids=solid_stack.element_ids)
    # all elements belong to the same stack so there should be only one solid stack
    assert len(solid_stacks) == 1

    solid_stacks = solid_stack_provider.get_solid_stacks(element_ids=[110, 113])
    assert len(solid_stacks) == 2


def test_solid_stack_with_dropoffs(dpf_server):
    """
    Test solid stack feature with drop-off elements
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Solid stack feature requires DPF server 10.0 or later.")
    composite_model = CompositeModel(get_file_paths(), server=dpf_server)
    solid_stack_provider = SolidStackProvider(
        composite_model.get_mesh(), composite_model.get_layup_operator()
    )

    solid_stack = solid_stack_provider.get_solid_stack(ELEMENT_OF_DROPOFF_STACK)
    print(f"Solid stack of element 113: {solid_stack}")
    assert solid_stack.number_of_elements == 8
    assert solid_stack.element_ids == [202, 186, 38, 247, 248, 88, 122, 154]
    assert solid_stack.number_of_analysis_plies == 10
    assert solid_stack.element_wise_analysis_plies == {
        202: ["P1L1__woven down 45", "P1L1__woven down -45"],
        186: ["P1L1__ud down 0"],
        38: ["P1L1__woven up 45", "P1L1__woven up -45"],
        247: ["P1L1__ud up 0"],
        248: ["P1L1__ud up 0"],
        88: ["P1L1__Honeycomb up 5mm"],
        122: ["P1L1__ud up 0.2"],
        154: ["P1L1__woven up -45.2", "P1L1__woven up 45.2"],
    }
    assert solid_stack.element_wise_levels == {
        202: 0,
        186: 1,
        38: 2,
        247: 3,
        248: 3,
        88: 4,
        122: 5,
        154: 6,
    }
    ref_ply_thicknesses = {
        202: [0.0002499281471069403, 0.0002499281471069403],
        186: [0.00020000000000000004],
        38: [0.00025000000000000017, 0.00025000000000000017],
        247: [5.000000000000002e-05],
        248: [5.000000000000002e-05],
        88: [0.004998642778686648],
        122: [0.0001999389250408988],
        154: [0.00025005356360532227, 0.00025005356360532227],
    }
    assert len(solid_stack.element_ply_thicknesses) == len(ref_ply_thicknesses)
    for element, thicknesses in solid_stack.element_ply_thicknesses.items():
        np.testing.assert_allclose(thicknesses, ref_ply_thicknesses[element], rtol=1e-6, atol=1e-8)

    assert solid_stack.element_ids_per_level == {
        0: [202],
        1: [186],
        2: [38],
        3: [247, 248],
        4: [88],
        5: [122],
        6: [154],
    }


def test_solid_stack_with_cutoffs(dpf_server):
    """
    Test solid stack feature with cut-off elements
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Solid stack feature requires DPF server 10.0 or later.")
    composite_model = CompositeModel(get_file_paths(), server=dpf_server)
    solid_stack_provider = SolidStackProvider(
        composite_model.get_mesh(), composite_model.get_layup_operator()
    )

    solid_stack = solid_stack_provider.get_solid_stack(ELEMENT_OF_CUTOFF_STACK)
    print(f"Solid stack of element: {solid_stack}")
    assert solid_stack.number_of_elements == 17
    assert solid_stack.element_ids == [
        219,
        196,
        55,
        300,
        301,
        302,
        303,
        304,
        305,
        306,
        307,
        308,
        309,
        332,
        333,
        351,
        352,
    ]
    assert solid_stack.number_of_analysis_plies == 9
    assert solid_stack.element_wise_analysis_plies == {
        219: ["P1L1__woven down 45", "P1L1__woven down -45"],
        196: ["P1L1__ud down 0"],
        55: ["P1L1__woven up 45", "P1L1__woven up -45"],
        300: ["P1L1__Honeycomb up 5mm"],
        301: ["P1L1__Honeycomb up 5mm"],
        302: ["P1L1__Honeycomb up 5mm"],
        303: ["P1L1__Honeycomb up 5mm"],
        304: ["P1L1__Honeycomb up 5mm"],
        305: ["P1L1__Honeycomb up 5mm"],
        306: ["P1L1__Honeycomb up 5mm"],
        307: ["P1L1__Honeycomb up 5mm"],
        308: ["P1L1__Honeycomb up 5mm"],
        309: ["P1L1__Honeycomb up 5mm"],
        332: ["P1L1__ud up 0.2"],
        333: ["P1L1__ud up 0.2"],
        351: ["P1L1__woven up -45.2", "P1L1__woven up 45.2"],
        352: ["P1L1__woven up -45.2", "P1L1__woven up 45.2"],
    }
    assert solid_stack.element_wise_levels == {
        219: 0,
        196: 1,
        55: 2,
        300: 3,
        301: 3,
        302: 3,
        303: 3,
        304: 3,
        305: 3,
        306: 3,
        307: 3,
        308: 3,
        309: 3,
        332: 4,
        333: 4,
        351: 5,
        352: 5,
    }
    ref_ply_thicknesses = {
        219: [0.0002499281471069403, 0.0002499281471069403],
        196: [0.00020000000000000004],
        55: [0.00025000000000000017, 0.00025000000000000017],
        300: [0.004999999999999999],
        301: [0.004999999999999999],
        302: [0.004999999999999999],
        303: [0.004999999999999999],
        304: [0.004999999999999999],
        305: [0.004999999999999999],
        306: [0.004999999999999999],
        307: [0.004999999999999999],
        308: [0.004999999999999999],
        309: [0.004999999999999999],
        332: [0.00019999999999999966],
        333: [0.00019999999999999966],
        351: [0.0002499999999999998, 0.0002499999999999998],
        352: [0.0002499999999999998, 0.0002499999999999998],
    }
    assert len(solid_stack.element_ply_thicknesses) == len(ref_ply_thicknesses)
    for element, thicknesses in solid_stack.element_ply_thicknesses.items():
        np.testing.assert_allclose(thicknesses, ref_ply_thicknesses[element], rtol=1e-6, atol=1e-8)


def test_sampling_point_solid_stack(dpf_server):
    """
    Test sampling point for solid model for a standard solid stack.

    The solid stack contains only layered elements.
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Sampling point for solids is supported since version 10.0 (2025 R2).")

    composite_model = CompositeModel(get_file_paths(), server=dpf_server)

    # Element with a standard solid stack (hex only)
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=get_fc(), element_id=ELEMENT_OF_LAYERED_STACK, time=1
    )

    plot = get_sampling_point_plot(sampling_point)
    # plot.figure.show()
    compare_results(sampling_point.results[0], ELEMENT_OF_LAYERED_STACK, version_older_than(dpf_server, "11.0"))


def test_sampling_point_solid_stack_with_dropoffs(dpf_server):
    """
    Test sampling point for solid model for a solid stack with drop-off elements.

    The drop-off elements need special handling to extract the results and layup information.
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Sampling point for solids is supported since version 10.0 (2025 R2).")

    composite_model = CompositeModel(get_file_paths(), server=dpf_server)

    # one drop-off with one element only
    # one drop-off which is split into two tetra elements
    for element_id in [113, ELEMENT_OF_DROPOFF_STACK]:
        sampling_point = composite_model.get_sampling_point(
            combined_criterion=get_fc(), element_id=element_id, time=1
        )

        plot = get_sampling_point_plot(sampling_point)
        # plot.figure.show()
        compare_results(sampling_point.results[0], element_id, version_older_than(dpf_server, "11.0"))


def test_sampling_point_solid_stack_with_cutoffs(dpf_server):
    """
    Test sampling point for solid model for a solid stack with cut-off elements.

    The cut-off elements need special handling to extract the results and layup information.
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Sampling point for solids is supported since version 10.0 (2025 R2).")
    composite_model = CompositeModel(get_file_paths(), server=dpf_server)

    # Element of a solid stack with cut-off elements
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=get_fc(), element_id=ELEMENT_OF_CUTOFF_STACK, time=1
    )

    plot = get_sampling_point_plot(sampling_point)
    # plot.figure.show()
    compare_results(sampling_point.results[0], ELEMENT_OF_CUTOFF_STACK, version_older_than(dpf_server, "11.0"))
