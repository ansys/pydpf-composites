import os
import pathlib

import ansys.dpf.core as dpf
import matplotlib.pyplot as plt
import numpy.testing

from ansys.dpf.composites.failure_criteria.combined_failure_criterion import (
    CombinedFailureCriterion,
)
from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion
from ansys.dpf.composites.result_definition import ResultDefinition
from ansys.dpf.composites.sampling_point import SamplingPoint


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

    rd = ResultDefinition(
        name="my first result definition",
        combined_failure_criterion=cfc,
        composite_definitions=[h5_server_path],
        rst_files=[rst_server_path],
        material_files=[material_server_path],
        element_scope=[3],
    )

    sampling_point = SamplingPoint(name="my first SP", result_definition=rd, server=dpf_server)

    sampling_point.update()

    indices = sampling_point.get_indices(["bottom", "top"])
    ref_indices = [0, 2, 3, 5, 6, 8, 9, 11, 12, 14]
    offsets = sampling_point.get_offsets(["bottom", "top"], 1.0)
    scaled_offsets = sampling_point.get_offsets(["bottom", "top"], 0.2)
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

    """Test default plots: result plot and polar plot"""
    fig, axes = sampling_point.get_result_plots(
        strain_components=["e1", "e12"],
        stress_components=["s13", "s23"],
        failure_components=["rf"],
        show_failure_modes=True,
        show_laminate=True,
        core_scale_factor=0.5,
        spots=["bottom", "top"],
    )

    fig, axis = sampling_point.get_polar_plot(["E1", "G12"])

    """Test manually created plots using the provided helpers"""
    interfaces = ["bottom", "top"]
    core_scale_factor = 1.0
    indices = sampling_point.get_indices(interfaces)
    offsets = sampling_point.get_offsets(interfaces, core_scale_factor)
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
        ax1, ["s13", "s23"], ["bottom", "top"], 0.5, "Out-of-plane shear stresses"
    )
    ax1.legend()
    plt.rcParams["hatch.linewidth"] = 0.2
    sampling_point.add_ply_sequence_to_plot(ax1, 0.5)
