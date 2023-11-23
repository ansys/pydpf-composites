import pathlib

from ansys.dpf.core import unit_systems
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FAILURE_LABEL, FailureOutput
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    get_composite_files_from_workbench_result_folder,
)
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    FailureModeEnum,
    MaxStressCriterion,
)
from ansys.dpf.composites.layup_info import LayerProperty, get_analysis_ply_index_to_name_map
from ansys.dpf.composites.layup_info.material_properties import MaterialProperty
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.server_helpers import version_equal_or_later, version_older_than

from .helper import Timer

SEPARATOR = "::"


def test_basic_functionality_of_composite_model(dpf_server, data_files, distributed_rst):
    if distributed_rst:
        # TODO: remove once backend issue #856638 is resolved
        pytest.xfail("The mesh property provider operator does not yet support distributed RST.")

    timer = Timer()

    composite_model = CompositeModel(data_files, server=dpf_server)
    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max stress", failure_criteria=[MaxStressCriterion()]
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
        LayerProperty.SHEAR_ANGLES: [0, 0, 0, 0, 0, 0],
        LayerProperty.ANGLES: [45, 0, 0, 0, 0, 45],
        LayerProperty.THICKNESSES: [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025],
    }
    element_id = 1
    for layer_property, value in expected_values.items():
        composite_model.get_property_for_all_layers(layer_property, element_id)

    assert composite_model.get_element_laminate_offset(element_id) == -0.00305
    analysis_ply_ids = [
        "P1L1__woven_45",
        "P1L1__ud_patch ns1",
        "P1L1__ud",
        "P1L1__core",
        "P1L1__ud.2",
        "P1L1__woven_45.2",
    ]
    assert composite_model.get_analysis_plies(element_id) == analysis_ply_ids

    assert composite_model.core_model is not None
    assert composite_model.get_mesh() is not None
    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion, element_id=1
    )

    assert [ply["id"] for ply in sampling_point.analysis_plies] == analysis_ply_ids

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


def test_model_with_multiple_timesteps(dpf_server):
    TEST_DATA_ROOT_DIR = (
        pathlib.Path(__file__).parent / "data" / "workflow_example" / "multiple_time_steps"
    )

    data_files = get_composite_files_from_workbench_result_folder(TEST_DATA_ROOT_DIR)

    composite_model = CompositeModel(data_files, server=dpf_server)

    combined_failure_criterion = CombinedFailureCriterion(
        "max stress", failure_criteria=[MaxStressCriterion()]
    )

    expected_data_by_time_index = {
        0: {1: 1.47927903, 2: 1.47927903, 3: 1.3673715, 4: 1.3673715},
        1: {1: 0.09834992, 2: 0.09834992, 3: 0.06173922, 4: 0.06173922},
    }

    for time_index, time in enumerate(composite_model.get_result_times_or_frequencies()):
        failure_output = composite_model.evaluate_failure_criteria(
            combined_criterion=combined_failure_criterion,
            composite_scope=CompositeScope(time=time),
        )

        # Note evaluate_failure_criteria supports only a single time step
        irf_field = failure_output.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})

        for element_id, expected_value in expected_data_by_time_index[time_index].items():
            assert irf_field.get_entity_data_by_id(element_id) == pytest.approx(expected_value)

        # Just check that the other fields are available
        def check_field_size(failure_label: FailureOutput):
            field = failure_output.get_field({FAILURE_LABEL: failure_label})
            assert len(field.scoping.ids) == 4

        check_field_size(FailureOutput.FAILURE_MODE)
        check_field_size(FailureOutput.MAX_LAYER_INDEX)

        if version_equal_or_later(dpf_server, "8.0"):
            check_field_size(FailureOutput.FAILURE_MODE_REF_SURFACE)
            check_field_size(FailureOutput.MAX_GLOBAL_LAYER_IN_STACK)
            check_field_size(FailureOutput.MAX_LOCAL_LAYER_IN_ELEMENT)
            check_field_size(FailureOutput.MAX_SOLID_ELEMENT_ID)


def test_assembly_model(dpf_server):
    """Verify the handling of assemblies."""

    timer = Timer()

    files = get_composite_files_from_workbench_result_folder(
        pathlib.Path(__file__).parent / "data" / "workflow_example" / "assembly"
    )

    solid_label = "Setup 3_solid"
    shell_label = "Setup 4_shell"

    composite_model = CompositeModel(files, server=dpf_server)
    timer.add("After Setup model")

    assert sorted(composite_model.composite_definition_labels) == sorted([solid_label, shell_label])

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStressCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criterion=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )

    timer.add("After get failure output")

    def check_output(failure_label: FailureOutput, expected_output: dict[int, float]):
        for element_id, expected_value in expected_output.items():
            failure_field = failure_output.get_field({FAILURE_LABEL: failure_label})
            assert failure_field.get_entity_data_by_id(element_id) == pytest.approx(expected_value)

    expected_output = {
        1: 1.11311715,
        2: 1.11311715,
        5: 1.85777034,
        6: 1.85777034,
        7: 0.0,
        8: 0.0,
        9: 0.62122959,
        10: 0.62122959,
    }
    check_output(FailureOutput.FAILURE_VALUE, expected_output)

    expected_modes = {
        1: FailureModeEnum.s1t.value,
        2: FailureModeEnum.s1t.value,
        5: FailureModeEnum.s2t.value,
        6: FailureModeEnum.s2t.value,
        7: FailureModeEnum.na.value,
        8: FailureModeEnum.na.value,
        9: FailureModeEnum.s2t.value,
        10: FailureModeEnum.s2t.value,
    }
    check_output(FailureOutput.FAILURE_MODE, expected_modes)

    expected_layer_index = {
        1: 2,
        2: 2,
        5: 2,
        6: 2,
        7: 1,
        8: 1,
        9: 1,
        10: 1,
    }

    if not version_equal_or_later(dpf_server, "7.1"):
        for element_id in expected_layer_index:
            # Older versions of the server returned a layer index that starts
            # at 0 instead of 1
            expected_layer_index[element_id] -= 1

    check_output(FailureOutput.MAX_LAYER_INDEX, expected_layer_index)

    expected_output_ref_surface = {
        1: 1.85777034,
        2: 1.85777034,
        3: 1.11311715,
        4: 1.11311715,
    }

    if version_equal_or_later(dpf_server, "8.0"):
        check_output(FailureOutput.FAILURE_VALUE_REF_SURFACE, expected_output_ref_surface)

        expected_output_local_layer = {
            1: 2,
            2: 2,
            3: 2,
            4: 2,
        }
        check_output(FailureOutput.MAX_LOCAL_LAYER_IN_ELEMENT, expected_output_local_layer)

        expected_output_global_layer = {
            1: 2,
            2: 2,
            3: 2,
            4: 2,
        }
        check_output(FailureOutput.MAX_GLOBAL_LAYER_IN_STACK, expected_output_global_layer)

        expected_output_solid_element = {
            1: 5,
            2: 6,
            3: 1,
            4: 2,
        }
        check_output(FailureOutput.MAX_SOLID_ELEMENT_ID, expected_output_solid_element)

    property_dict = composite_model.get_constant_property_dict(
        [MaterialProperty.Stress_Limits_Xt], composite_definition_label=solid_label
    )
    timer.add("After get property dict")

    assert property_dict[2][MaterialProperty.Stress_Limits_Xt] == pytest.approx(513000000.0)

    expected_element_info = {
        solid_label: {"element_ids": [5, 6, 7, 8, 9, 10], "element_type": 190},
        shell_label: {"element_ids": [1, 2], "element_type": 181},
    }

    if version_older_than(dpf_server, "7.0"):
        # loop over each part separately if the old server is used
        for composite_label in composite_model.composite_definition_labels:
            expected = expected_element_info[composite_label]
            all_layered_elements = (
                composite_model.get_all_layered_element_ids_for_composite_definition_label(
                    composite_label
                )
            )
            assert set(all_layered_elements) == set(expected["element_ids"])
            for element_id in all_layered_elements:
                element_info = composite_model.get_element_info(element_id, composite_label)
                assert element_info.is_layered
                assert element_info.element_type == expected["element_type"]

        assert len(get_analysis_ply_index_to_name_map(composite_model.get_mesh(shell_label))) == 5
        assert len(get_analysis_ply_index_to_name_map(composite_model.get_mesh(solid_label))) == 6
    else:
        # latest server
        all_layered_elements = (
            composite_model.get_all_layered_element_ids_for_composite_definition_label()
        )
        assert set(all_layered_elements) == set(
            expected_element_info[shell_label]["element_ids"]
            + expected_element_info[solid_label]["element_ids"]
        )

        for expected_elements in [
            expected_element_info[shell_label],
            expected_element_info[solid_label],
        ]:
            for element_id in expected_elements["element_ids"]:
                element_info = composite_model.get_element_info(element_id)
                assert element_info.is_layered
                assert element_info.element_type == expected_elements["element_type"]

        assert len(get_analysis_ply_index_to_name_map(composite_model.get_mesh())) == 11

    timer.add("After getting element_info")

    expected_values_shell = {
        LayerProperty.SHEAR_ANGLES: [0, 0, 0, 0, 0],
        LayerProperty.ANGLES: [45, 0, 0, 0, 45],
        LayerProperty.THICKNESSES: [0.00025, 0.0002, 0.005, 0.0002, 0.00025],
    }

    expected_values_solid = {
        LayerProperty.SHEAR_ANGLES: [0, 0, 0],
        LayerProperty.ANGLES: [45, 0, 0],
        LayerProperty.THICKNESSES: [0.00025, 0.0002, 0.0002],
    }

    shell_element_id = 1
    for layer_property, value in expected_values_shell.items():
        assert value == pytest.approx(
            composite_model.get_property_for_all_layers(
                layer_property, shell_element_id, shell_label
            )
        )

    solid_element_id = 5
    for layer_property, value in expected_values_solid.items():
        assert value == pytest.approx(
            composite_model.get_property_for_all_layers(
                layer_property, solid_element_id, solid_label
            )
        )

    assert composite_model.get_element_laminate_offset(shell_element_id, shell_label) == -0.00295

    if version_older_than(dpf_server, "7.0"):
        prefix = ""
    else:
        prefix = f"{shell_label}{SEPARATOR}"

    analysis_ply_ids_shell = [
        f"{prefix}P1L1__woven_45",
        f"{prefix}P1L1__ud",
        f"{prefix}P1L1__core",
        f"{prefix}P1L1__ud.2",
        f"{prefix}P1L1__woven_45.2",
    ]

    assert (
        composite_model.get_analysis_plies(shell_element_id, shell_label) == analysis_ply_ids_shell
    )

    assert composite_model.core_model is not None
    if version_older_than(dpf_server, "7.0"):
        assert composite_model.get_mesh(shell_label) is not None
        assert composite_model.get_mesh(solid_label) is not None
    else:
        assert composite_model.get_mesh() is not None

    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion,
        element_id=1,
        composite_definition_label=shell_label,
    )

    sampling_point.run()
    assert [ply["id"] for ply in sampling_point.analysis_plies] == [
        ply_id.replace(f"{shell_label}{SEPARATOR}", "") for ply_id in analysis_ply_ids_shell
    ]

    assert composite_model.get_element_laminate_offset(
        solid_element_id, solid_label
    ) == pytest.approx(0.0)
    if version_older_than(dpf_server, "7.0"):
        prefix = ""
    else:
        prefix = f"{solid_label}{SEPARATOR}"

    analysis_ply_ids_solid = [
        f"{prefix}P1L1__woven_45",
        f"{prefix}P1L1__ud_patch ns1",
        f"{prefix}P1L1__ud",
    ]

    assert (
        composite_model.get_analysis_plies(solid_element_id, solid_label) == analysis_ply_ids_solid
    )

    timer.add("After getting properties")
    timer.summary()


def test_failure_measures(dpf_server, data_files):
    """Verify that all failure measure names are compatible with the backend"""
    composite_model = CompositeModel(data_files, server=dpf_server)
    combined_failure_criterion = CombinedFailureCriterion(
        "max stress", failure_criteria=[MaxStressCriterion()]
    )

    for v in FailureMeasureEnum:
        failure_output = composite_model.evaluate_failure_criteria(
            combined_criterion=combined_failure_criterion,
            composite_scope=CompositeScope(),
            measure=v,
        )


def test_failure_criteria_evaluation_default_unit_system(dpf_server):
    """
    Test if failure criteria can be evaluated if the unit system
    is not part of the rst (because the project was created from mapdl)
    """
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell_mapdl"
    rst_path = TEST_DATA_ROOT_DIR / "linear_shell_analysis_model.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    files = ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )
    composite_model = CompositeModel(
        files, server=dpf_server, default_unit_system=unit_systems.solver_mks
    )
    cfc = CombinedFailureCriterion("max stress", failure_criteria=[MaxStressCriterion()])

    failure_container = composite_model.evaluate_failure_criteria(cfc)
