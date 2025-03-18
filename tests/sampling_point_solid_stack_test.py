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

import os
import pathlib

from ansys.dpf.core import unit_systems
import matplotlib.pyplot as plt
import numpy as np
import numpy.testing
import pytest

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput, Spot
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    PuckCriterion,
    FaceSheetWrinklingCriterion,
    CoreFailureCriterion
)
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.sampling_point_types import FailureResult

from .helper import get_basic_shell_files


def test_sampling_point_solid_stack(dpf_server):
    """
    Test sampling point for solid model for a standard solid stack.

    The solid stack contains only layered elements.
    """

    TEST_DATA_ROOT_DIR = r"D:\tmp\small_solid_model_files\dp0\SYS\MECH"
    rst_paths = [os.path.join(TEST_DATA_ROOT_DIR, "file.rst")]
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "ACPSolidModel_SolidModel.1.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "material.engd")

    files = ContinuousFiberCompositesFiles(
        rst=rst_paths,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    composite_model = CompositeModel(files, server=dpf_server)

    cfc = CombinedFailureCriterion("combined")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())
    cfc.insert(PuckCriterion())
    cfc.insert(FaceSheetWrinklingCriterion())
    cfc.insert(CoreFailureCriterion())

    # Element with a standard solid stack (hex only)
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=cfc,
        element_id=110,
        time=1
    )

    plot = sampling_point.get_result_plots(
        strain_components=["e1", "e2", "e12"],
        stress_components=["s1", "s2", "s12"],
        failure_components=[FailureMeasureEnum.INVERSE_RESERVE_FACTOR],
        core_scale_factor=0.2,
        show_failure_modes=True,
    )
    plot.figure.show()
    res = sampling_point.results
    print(res[0]['results']['strains']['e12'])



def test_sampling_point_solid_stack_with_dropoffs(dpf_server):
    """
    Test sampling point for solid model for a solid stack with drop-off elements.

    The drop-off elements need special handling to extract the results and layup information.
    """
    TEST_DATA_ROOT_DIR = r"D:\tmp\small_solid_model_files\dp0\SYS\MECH"
    rst_paths = [os.path.join(TEST_DATA_ROOT_DIR, "file.rst")]
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "ACPSolidModel_SolidModel.1.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "material.engd")

    files = ContinuousFiberCompositesFiles(
        rst=rst_paths,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    composite_model = CompositeModel(files, server=dpf_server)

    cfc = CombinedFailureCriterion("combined")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())
    cfc.insert(PuckCriterion())
    cfc.insert(FaceSheetWrinklingCriterion())
    cfc.insert(CoreFailureCriterion())

    for element_id in [113, 154]:
        sampling_point = composite_model.get_sampling_point(
            combined_criterion=cfc,
            element_id=element_id,
            time=1
        )

        plot = sampling_point.get_result_plots(
            strain_components=["e1", "e2", "e12"],
            stress_components=["s1", "s2", "s12"],
            failure_components=[FailureMeasureEnum.INVERSE_RESERVE_FACTOR],
            core_scale_factor=0.2,
            show_failure_modes=True,
        )
        plot.figure.show()
        res = sampling_point.results
        print(res[0]['results']['strains']['e12'])


def test_sampling_point_solid_stack_with_cutoffs(dpf_server):
    """
    Test sampling point for solid model for a solid stack with cut-off elements.

    The cut-off elements need special handling to extract the results and layup information.
    """
    TEST_DATA_ROOT_DIR = r"D:\tmp\small_solid_model_files\dp0\SYS\MECH"
    rst_paths = [os.path.join(TEST_DATA_ROOT_DIR, "file.rst")]
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "ACPSolidModel_SolidModel.1.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "Setup", "material.engd")

    files = ContinuousFiberCompositesFiles(
        rst=rst_paths,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    composite_model = CompositeModel(files, server=dpf_server)

    cfc = CombinedFailureCriterion("combined")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())
    cfc.insert(PuckCriterion())
    cfc.insert(FaceSheetWrinklingCriterion())
    cfc.insert(CoreFailureCriterion())

    # Element of a solid stack with cut-off elements
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=cfc,
        element_id=219,
        time=1
    )

    plot = sampling_point.get_result_plots(
        strain_components=["e1", "e2", "e12"],
        stress_components=["s1", "s2", "s12"],
        failure_components=[FailureMeasureEnum.INVERSE_RESERVE_FACTOR],
        core_scale_factor=0.2,
        show_failure_modes=True,
    )
    plot.figure.show()
    res = sampling_point.results
    print(res[0]['results']['strains']['e12'])
