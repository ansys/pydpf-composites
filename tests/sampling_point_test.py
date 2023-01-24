import os
import pathlib

import ansys.dpf.core as dpf
import matplotlib.pyplot as plt
import numpy as np
import numpy.testing
import pytest

from ansys.dpf.composites.composite_data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.enums import FailureOutput, Spot
from ansys.dpf.composites.example_helper import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.failure_criteria.combined_failure_criterion import (
    CombinedFailureCriterion,
)
from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion
from ansys.dpf.composites.result_definition import ResultDefinition, ResultDefinitionScope
from ansys.dpf.composites.sampling_point import FailureResult, SamplingPoint


def test_sampling_point(dpf_server):
    """Basic test with a running server"""

    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=dpf_server)
    h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=dpf_server)
    material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=dpf_server)

    cfc = CombinedFailureCriterion("max strain & max stress")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())

    scope = ResultDefinitionScope(composite_definition=h5_server_path, element_scope=[3])

    rd = ResultDefinition(
        name="my first result definition",
        combined_failure_criterion=cfc,
        rst_file=rst_server_path,
        material_file=material_server_path,
        composite_scopes=[scope],
    )

    sampling_point = SamplingPoint(name="my first SP", result_definition=rd, server=dpf_server)

    indices = sampling_point.get_indices([Spot.bottom, Spot.top])
    ref_indices = [0, 2, 3, 5, 6, 8, 9, 11, 12, 14]
    offsets = sampling_point.get_offsets_by_spots([Spot.bottom, Spot.top], 1.0)
    scaled_offsets = sampling_point.get_offsets_by_spots([Spot.bottom, Spot.top], 0.2)
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
            mode="e12",
            irf=pytest.approx(2.248462289571762),
            rf=pytest.approx(0.4447483974438629),
            mos=pytest.approx(-0.5552516025561371),
        ),
        FailureResult(
            mode="e1t",
            irf=pytest.approx(1.522077660182279),
            rf=pytest.approx(0.6569967000765541),
            mos=pytest.approx(-0.3430032999234459),
        ),
        FailureResult(mode="na", irf=0.0, rf=1000.0, mos=999.0),
        FailureResult(
            mode="e12",
            irf=pytest.approx(0.1853588231218358),
            rf=pytest.approx(5.394941460880462),
            mos=pytest.approx(4.394941460880462),
        ),
        FailureResult(
            mode="s2c",
            irf=pytest.approx(0.3256845400457666),
            rf=pytest.approx(3.07045584619852),
            mos=pytest.approx(2.07045584619852),
        ),
    ]
    assert critical_failures == ref

    """Test default plots: result plot and polar plot"""
    fig, axes = sampling_point.get_result_plots(
        strain_components=["e1", "e12"],
        stress_components=["s13", "s23"],
        failure_components=["rf"],
        show_failure_modes=True,
        create_laminate_plot=True,
        core_scale_factor=0.5,
        spots=[Spot.bottom, Spot.top],
    )

    fig, axis = sampling_point.get_polar_plot(["E1", "G12"])

    """Test manually created plots using the provided helpers"""
    spots = [Spot.bottom, Spot.top]
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
        ax1, ["s13", "s23"], [Spot.bottom, Spot.top], 0.5, "Out-of-plane shear stresses"
    )
    ax1.legend()
    plt.rcParams["hatch.linewidth"] = 0.2
    sampling_point.add_ply_sequence_to_plot(ax1, 0.5)


def test_sampling_point_with_numpy_types(dpf_server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    composite_files = ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )

    files = upload_continuous_fiber_composite_files_to_server(
        data_files=composite_files, server=dpf_server
    )
    cfc = CombinedFailureCriterion(
        "max strain & max stress", [MaxStrainCriterion(), MaxStressCriterion()]
    )
    composite_model = CompositeModel(files, server=dpf_server)

    failure_container = composite_model.evaluate_failure_criteria(cfc)
    irfs = failure_container.get_field({"failure_label": FailureOutput.failure_value})
    critical_element_id = irfs.scoping.ids[np.argmax(irfs.data)]
    sp = composite_model.get_sampling_point(cfc, critical_element_id)
    assert max(sp.s1) == pytest.approx(2840894080.0, 1e-8)
