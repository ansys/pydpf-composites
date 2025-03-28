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
)
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.sampling_point_types import FailureResult

from .helper import get_basic_shell_files


def test_sampling_point(dpf_server, distributed_rst):
    """Basic test with a running server"""

    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"
    if distributed_rst:
        rst_paths = [
            os.path.join(TEST_DATA_ROOT_DIR, f"distributed_shell{i}.rst") for i in range(2)
        ]
    else:
        rst_paths = [os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")]
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    files = ContinuousFiberCompositesFiles(
        result_files=rst_paths,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    composite_model = CompositeModel(files, server=dpf_server)

    cfc = CombinedFailureCriterion("max strain & max stress")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())

    sampling_point = composite_model.get_sampling_point(cfc, 3)

    indices = sampling_point.get_indices([Spot.BOTTOM, Spot.TOP])
    ref_indices = [0, 2, 3, 5, 6, 8, 9, 11, 12, 14]
    offsets = sampling_point.get_offsets_by_spots([Spot.BOTTOM, Spot.TOP], 1.0)
    scaled_offsets = sampling_point.get_offsets_by_spots([Spot.BOTTOM, Spot.TOP], 0.2)
    ref_offsets = [
        -0.00295,
        -0.0027,
        -0.0027,
        -0.0025,
        -0.0025,
        0.0025,
        0.0025,
        0.0027,
        0.0027,
        0.00295,
    ]
    ref_scaled_offsets = [
        -0.00295,
        -0.0027,
        -0.0027,
        -0.0025,
        -0.0025,
        -0.0015,
        -0.0015,
        -0.0013,
        -0.0013,
        -0.00105,
    ]

    assert indices == ref_indices
    numpy.testing.assert_allclose(offsets, ref_offsets)
    numpy.testing.assert_allclose(scaled_offsets, ref_scaled_offsets)

    """ply-wise max failures"""
    critical_failures = sampling_point.get_ply_wise_critical_failures()
    assert len(critical_failures) == sampling_point.number_of_plies
    ref = [
        FailureResult(
            "e12",
            pytest.approx(2.248462289571762),
            pytest.approx(0.4447483974438629),
            pytest.approx(-0.5552516025561371),
        ),
        FailureResult(
            "e1t",
            pytest.approx(1.522077660182279),
            pytest.approx(0.6569967000765541),
            pytest.approx(-0.3430032999234459),
        ),
        FailureResult("na", 0.0, 1000.0, 999.0),
        FailureResult(
            "e12",
            pytest.approx(0.1853588231218358),
            pytest.approx(5.394941460880462),
            pytest.approx(4.394941460880462),
        ),
        FailureResult(
            "s2c",
            pytest.approx(0.3256845400457666),
            pytest.approx(3.07045584619852),
            pytest.approx(2.07045584619852),
        ),
    ]
    assert critical_failures == ref

    """Test default plots: result plot and polar plot"""
    sampling_point.get_result_plots(
        strain_components=["e1", "e12"],
        stress_components=["s13", "s23"],
        failure_components=[FailureMeasureEnum.RESERVE_FACTOR],
        show_failure_modes=True,
        create_laminate_plot=True,
        core_scale_factor=0.5,
        spots=[Spot.BOTTOM, Spot.TOP],
    )

    sampling_point.get_polar_plot(["E1", "G12"])

    """Test manually created plots using the provided helpers"""
    spots = [Spot.BOTTOM, Spot.TOP]
    core_scale_factor = 1.0
    indices = sampling_point.get_indices(spots)
    offsets = sampling_point.get_offsets_by_spots(spots, core_scale_factor)
    s13 = sampling_point.s13[indices]

    fig, ax1 = plt.subplots()
    plt.rcParams["hatch.linewidth"] = 0.2
    line = ax1.plot(s13, offsets, label="s13")
    ax1.set_yticks([])
    ax1.legend()
    ax1.set_title("Interlaminar shear stresses s13")
    sampling_point.add_ply_sequence_to_plot(ax1, core_scale_factor)

    fig, ax1 = plt.subplots()
    sampling_point.add_results_to_plot(
        ax1, ["s13", "s23"], [Spot.BOTTOM, Spot.TOP], 0.5, "Out-of-plane shear stresses"
    )
    ax1.legend()
    plt.rcParams["hatch.linewidth"] = 0.2
    sampling_point.add_ply_sequence_to_plot(ax1, 0.5)


def test_sampling_point_result_plots(dpf_server):
    """Ensure that get_result_plots works if only one plot is selected."""
    files = get_basic_shell_files()

    cfc = CombinedFailureCriterion(
        "max strain & max stress", [MaxStrainCriterion(), MaxStressCriterion()]
    )
    composite_model = CompositeModel(files, server=dpf_server)

    """Test axes plot with only one axis"""
    sp = composite_model.get_sampling_point(cfc, 1)
    plot_obj = sp.get_result_plots(
        create_laminate_plot=True, strain_components=[], stress_components=[], failure_components=[]
    )
    plot_obj = sp.get_result_plots(
        create_laminate_plot=False,
        strain_components=["e1"],
        stress_components=[],
        failure_components=[],
    )
    plot_obj = sp.get_result_plots(
        create_laminate_plot=False,
        strain_components=[],
        stress_components=["s1"],
        failure_components=[],
    )
    plot_obj = sp.get_result_plots(
        create_laminate_plot=False,
        strain_components=[],
        stress_components=[],
        failure_components=[FailureMeasureEnum.MARGIN_OF_SAFETY],
    )


def test_sampling_point_with_numpy_types(dpf_server):
    composite_files = files = get_basic_shell_files()

    cfc = CombinedFailureCriterion(
        "max strain & max stress", [MaxStrainCriterion(), MaxStressCriterion()]
    )
    composite_model = CompositeModel(composite_files, server=dpf_server)

    failure_container = composite_model.evaluate_failure_criteria(cfc)
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    critical_element_id = irfs.scoping.ids[np.argmax(irfs.data)]
    sp = composite_model.get_sampling_point(cfc, critical_element_id)
    assert max(sp.s1) == pytest.approx(2840894080.0, 1e-8)


def test_sampling_point_and_time_scoping(dpf_server):
    """Ensure that time scoping is handled correctly."""
    files = get_basic_shell_files(two_load_steps=True)

    composite_model = CompositeModel(files, server=dpf_server)
    cfc = CombinedFailureCriterion(
        "combined",
        failure_criteria=[
            MaxStressCriterion(s1=True, s2=True, s3=True, s12=True, s13=True, s23=True)
        ],
    )
    # expect max IRF at element 1 over all plies
    time_id_and_expected_max_irf = {
        1.0: 1.4792790998492324,
        1.5: 0.75120980930142467,
        2.0: 0.09834992555064767,
    }

    for time, expected_max_irf in time_id_and_expected_max_irf.items():
        sp = composite_model.get_sampling_point(combined_criterion=cfc, element_id=1, time=time)
        assert max(sp.inverse_reserve_factor) == pytest.approx(expected_max_irf, abs=1e-6)


def test_sampling_point_with_default_unit_system(dpf_server):
    """
    Test if a sampling point can be evaluated if the unit system
    is not part of the rst (because the project was created from mapdl)
    """
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell_mapdl"
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "linear_shell_analysis_model.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    composite_files = ContinuousFiberCompositesFiles(
        result_files=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    cfc = CombinedFailureCriterion(
        "max strain & max stress", [MaxStrainCriterion(), MaxStressCriterion()]
    )
    composite_model = CompositeModel(
        composite_files, server=dpf_server, default_unit_system=unit_systems.solver_mks
    )

    failure_container = composite_model.evaluate_failure_criteria(cfc)
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    critical_element_id = irfs.scoping.ids[np.argmax(irfs.data)]
    sp = composite_model.get_sampling_point(cfc, critical_element_id)
    sp.get_polar_plot()
