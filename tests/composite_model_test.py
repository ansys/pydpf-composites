import os
import pathlib
from typing import List, Union

import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    get_composite_files_from_workbench_result_folder,
)
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.layup_info import LayerProperty, get_analysis_ply_index_to_name_map
from ansys.dpf.composites.layup_info.material_properties import MaterialProperty
from ansys.dpf.composites.result_definition import FailureMeasureEnum

from .helper import ContinuousFiberCompositesFiles, Timer

SEPARATOR = "::"

@pytest.fixture
def data_files(distributed_rst):
    # Using lightweight data for unit tests. Replace by get_ger_data_data_files
    # for actual performance tests
    # return get_ger_data_files()
    return get_dummy_data_files(distributed=distributed_rst)


def get_assembly_data_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "assembly"

    rst_path = TEST_DATA_ROOT_DIR / "file.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    solid_definitions = TEST_DATA_ROOT_DIR / "ACPSolidModel_SM.h5"
    mapping_shell_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.mapping"
    mapping_solid_path = TEST_DATA_ROOT_DIR / "ACPSolidModel_SM.mapping"

    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite={
            "shell": CompositeDefinitionFiles(definition=h5_path, mapping=mapping_shell_path),
            "solid": CompositeDefinitionFiles(
                definition=solid_definitions, mapping=mapping_solid_path
            ),
        },
        engineering_data=material_path,
    )


def get_dummy_data_files(distributed: bool = False):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    if distributed:
        rst_path: Union[str, List[str]] = [
            os.path.join(TEST_DATA_ROOT_DIR, f"distributed_shell{i}.rst") for i in range(2)
        ]
    else:
        rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    return ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )


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

    properyt_dict = composite_model.get_constant_property_dict([MaterialProperty.Stress_Limits_Xt])

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

    timer.add("After getting properties")

    timer.summary()


def test_assembly_model(dpf_server):
    timer = Timer()

    files = get_composite_files_from_workbench_result_folder(
        pathlib.Path(__file__).parent / "data" / "workflow_example" / "assembly"
    )

    solid_label = "Setup 3_solid"
    shell_label = "Setup 4_shell"

    composite_model = CompositeModel(files, server=dpf_server)
    timer.add("After Setup model")

    assert composite_model.composite_definition_labels == [solid_label, shell_label]

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStressCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criterion=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )

    timer.add("After get failure output")

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

    for element_id, expected_value in expected_output.items():
        assert failure_output[1].get_entity_data_by_id(element_id) == pytest.approx(expected_value)

    properyt_dict = composite_model.get_constant_property_dict(
        [MaterialProperty.Stress_Limits_Xt], composite_definition_label=solid_label
    )
    timer.add("After get property dict")

    assert properyt_dict[2][MaterialProperty.Stress_Limits_Xt] == pytest.approx(513000000.0)

    expected_solids = {"element_ids": [5, 6, 7, 8, 9, 10], "element_type": 190}
    expected_shells = {"element_ids": [1, 2], "element_type": 181}

    all_layered_elements = (
        composite_model.get_all_layered_element_ids_for_composite_definition_label()
    )
    assert set(all_layered_elements) == set(expected_shells["element_ids"] + expected_solids["element_ids"])

    for expected_elements in [expected_shells, expected_solids]:
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
                layer_property, shell_element_id
            )
        )

    solid_element_id = 5
    for layer_property, value in expected_values_solid.items():
        assert value == pytest.approx(
            composite_model.get_property_for_all_layers(
                layer_property, solid_element_id
            )
        )

    assert composite_model.get_element_laminate_offset(shell_element_id) == -0.00295
    analysis_ply_ids_shell = [
        f'{shell_label}{SEPARATOR}P1L1__woven_45',
        f'{shell_label}{SEPARATOR}P1L1__ud',
        f'{shell_label}{SEPARATOR}P1L1__core',
        f'{shell_label}{SEPARATOR}P1L1__ud.2',
        f'{shell_label}{SEPARATOR}P1L1__woven_45.2'
    ]

    assert (
        composite_model.get_analysis_plies(shell_element_id) == analysis_ply_ids_shell
    )

    assert composite_model.core_model is not None
    assert composite_model.get_mesh() is not None
    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion,
        element_id=1
    )

    sampling_point.run()
    assert [ply["id"] for ply in sampling_point.analysis_plies] == analysis_ply_ids_shell

    assert composite_model.get_element_laminate_offset(
        solid_element_id
    ) == pytest.approx(0.0)
    analysis_ply_ids_solid = [
        f"{solid_label}{SEPARATOR}P1L1__woven_45",
        f"{solid_label}{SEPARATOR}P1L1__ud_patch ns1",
        f"{solid_label}{SEPARATOR}P1L1__ud",
    ]

    assert (
        composite_model.get_analysis_plies(solid_element_id) == analysis_ply_ids_solid
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


def test_composite_model_element_scope(dpf_server, data_files):
    """Ensure that the element IDs of the scope can be of any type (e.g. np.int)"""
    composite_model = CompositeModel(data_files, server=dpf_server)
    cfc = CombinedFailureCriterion("max stress", failure_criteria=[MaxStressCriterion()])

    failure_container = composite_model.evaluate_failure_criteria(cfc)
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    min_id = irfs.scoping.ids[np.argmin(irfs.data)]
    max_id = irfs.scoping.ids[np.argmax(irfs.data)]

    composite_scope = CompositeScope(elements=[min_id, max_id])
    max_container = composite_model.evaluate_failure_criteria(cfc, composite_scope)
    max_irfs = max_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    assert len(max_irfs.data) == 2
    assert max_irfs.get_entity_data_by_id(min_id)[0] == pytest.approx(min(irfs.data), 1e-8)
    assert max_irfs.get_entity_data_by_id(max_id)[0] == pytest.approx(max(irfs.data), 1e-8)


def test_composite_model_named_selection_scope(dpf_server, data_files, distributed_rst):
    """Ensure that the scoping by Named Selection is supported"""
    if distributed_rst:
        # TODO: remove once backend issue #856638 is resolved
        pytest.xfail("The mesh property provider operator does not yet support distributed RST.")

    composite_model = CompositeModel(data_files, server=dpf_server)

    ns_name = "NS_ELEM"
    assert ns_name in composite_model.get_mesh().available_named_selections
    ns_scope = composite_model.get_mesh().named_selection(ns_name)
    assert list(ns_scope.ids) == [2, 3]

    cfc = CombinedFailureCriterion("max stress", failure_criteria=[MaxStressCriterion()])

    scope = CompositeScope(named_selections=[ns_name])
    failure_container = composite_model.evaluate_failure_criteria(cfc, scope)
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    assert len(irfs.data) == 2
    assert irfs.data[0] == pytest.approx(1.4792790331384016, 1e-8)
    assert irfs.data[1] == pytest.approx(1.3673715033617213, 1e-8)
