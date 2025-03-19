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
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.sampling_point_types import SamplingPoint, SamplingPointFigure
from ansys.dpf.composites.server_helpers import version_older_than

from .helper import compare_sampling_point_results

TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "solid_model"


def get_file_paths() -> ContinuousFiberCompositesFiles:
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "file.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPSolidModel_SolidModel.1.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    files = ContinuousFiberCompositesFiles(
        rst=rst_path,
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


def compare_results(current, element_id) -> None:
    with open(os.path.join(TEST_DATA_ROOT_DIR, f"ref_{element_id}.txt")) as f:
        reference = json.loads(json.load(f))

    compare_sampling_point_results(reference, current, with_polar_properties=False)


def get_sampling_point_plot(sampling_point: SamplingPoint) -> SamplingPointFigure:
    return sampling_point.get_result_plots(
        strain_components=["e1", "e2", "e12"],
        stress_components=["s1", "s2", "s12"],
        failure_components=[FailureMeasureEnum.INVERSE_RESERVE_FACTOR],
        core_scale_factor=0.2,
        show_failure_modes=True,
    )


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
        combined_criterion=get_fc(), element_id=110, time=1
    )

    plot = get_sampling_point_plot(sampling_point)
    # plot.figure.show()
    compare_results(sampling_point.results[0], 110)


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
    for element_id in [113, 154]:
        sampling_point = composite_model.get_sampling_point(
            combined_criterion=get_fc(), element_id=element_id, time=1
        )

        plot = get_sampling_point_plot(sampling_point)
        # plot.figure.show()
        compare_results(sampling_point.results[0], element_id)


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
        combined_criterion=get_fc(), element_id=219, time=1
    )

    plot = get_sampling_point_plot(sampling_point)
    # plot.figure.show()
    compare_results(sampling_point.results[0], 219)
