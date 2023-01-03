import os
import pathlib

import ansys.dpf.core as dpf
import pytest

from ansys.dpf.composites import MaterialProperty
from ansys.dpf.composites.composite_data_sources import CompositeFiles
from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.enums import LayerProperty
from ansys.dpf.composites.example_helper.example_helper import (
    upload_continuous_fiber_composite_files_to_server,
)
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.layup_info import get_analysis_ply_index_to_name_map

from .helper import ContinuousFiberCompositesFiles, Timer


def get_data_files():
    # Using lightweight data for unit tests. Replace by get_ger_data_data_files
    # for actual performance tests
    # return get_ger_data_files()
    return get_dummy_data_files()


def get_assembly_data_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "assembly"

    rst_path = TEST_DATA_ROOT_DIR / "file.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    mapping_shell_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.mapping"
    mapping_solid_path = TEST_DATA_ROOT_DIR / "ACPSolidModel_SM.mapping"

    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite_files=[
            CompositeFiles(composite_definitions=h5_path, mapping_files=[mapping_shell_path])
        ],
        engineering_data=material_path,
    )


def get_dummy_data_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    return ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite_files=[CompositeFiles(composite_definitions=h5_path)],
        engineering_data=material_path,
    )


def get_test_data(dpf_server):
    files = get_data_files()
    rst_path = dpf.upload_file_in_tmp_folder(files.rst, server=dpf_server)

    rst_data_source = dpf.DataSources(rst_path)

    strain_operator = dpf.Operator("EPEL")
    strain_operator.inputs.data_sources(rst_data_source)
    strain_operator.inputs.bool_rotate_to_global(False)

    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)
    field = fields_container[0]
    return field


def test_basic_functionality_of_composite_model(dpf_server):
    timer = Timer()

    files = get_data_files()
    files = upload_continuous_fiber_composite_files_to_server(data_files=files, server=dpf_server)
    timer.add("After Upload files")

    composite_model = CompositeModel(files, server=dpf_server)
    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStressCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criteria=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )

    properyt_dict = composite_model.get_constant_property_dict([MaterialProperty.Stress_Limits_Xt])

    timer.add("After get property dict")

    element_infos = [
        composite_model.get_element_info(element_id)
        for element_id in composite_model.mesh.elements.scoping.ids
    ]
    get_analysis_ply_index_to_name_map(composite_model.mesh)

    timer.add("After getting element_info")

    expected_values = {
        LayerProperty.shear_angles: [0, 0, 0, 0, 0, 0],
        LayerProperty.angles: [45, 0, 0, 0, 0, 45],
        LayerProperty.thicknesses: [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025],
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
    assert composite_model.mesh is not None
    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criteria=combined_failure_criterion, element_id=1
    )

    assert [ply["id"] for ply in sampling_point.analysis_plies] == analysis_ply_ids

    timer.add("After getting properties")

    timer.summary()


def test_assembly_model(dpf_server):
    timer = Timer()

    files = get_assembly_data_files()
    files = upload_continuous_fiber_composite_files_to_server(data_files=files, server=dpf_server)
    timer.add("After Upload files")

    composite_model = CompositeModel(files, server=dpf_server)
    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStressCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criteria=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )
    timer.add("After get failure output")

    assert failure_output.get_field({"failure_label": 0}).data[0] == pytest.approx(211.0)

    properyt_dict = composite_model.get_constant_property_dict([MaterialProperty.Stress_Limits_Xt])
    timer.add("After get property dict")

    assert properyt_dict[2][MaterialProperty.Stress_Limits_Xt] == pytest.approx(513000000.0)

    element_info = composite_model.get_element_info(1)

    assert element_info.element_type == 181

    analysis_ply_map = get_analysis_ply_index_to_name_map(composite_model.mesh)
    assert analysis_ply_map[0] == "P1L1__woven_45"

    timer.add("After getting element_info")

    expected_values = {
        LayerProperty.shear_angles: [0, 0, 0, 0, 0, 0],
        LayerProperty.angles: [45, 0, 0, 0, 0, 45],
        LayerProperty.thicknesses: [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025],
    }
    element_id = 1
    for layer_property, value in expected_values.items():
        composite_model.get_property_for_all_layers(layer_property, element_id)

    assert composite_model.get_element_laminate_offset(element_id) == -0.00295
    analysis_ply_ids = [
        "P1L1__woven_45",
        "P1L1__ud",
        "P1L1__core",
        "P1L1__ud.2",
        "P1L1__woven_45.2",
    ]
    assert composite_model.get_analysis_plies(element_id) == analysis_ply_ids

    assert composite_model.core_model is not None
    assert composite_model.mesh is not None
    assert composite_model.data_sources is not None
    sampling_point = composite_model.get_sampling_point(
        combined_criteria=combined_failure_criterion, element_id=1
    )

    assert [ply["id"] for ply in sampling_point.analysis_plies] == analysis_ply_ids

    timer.add("After getting properties")

    timer.summary()
