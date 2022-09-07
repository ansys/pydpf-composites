import os
import pathlib

import ansys.dpf.core as dpf
import pytest

from .utils import get_basic_combined_failure_criterion


def test_basic_workflow(dpf_server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=dpf_server)

    h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=dpf_server)
    material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=dpf_server)

    rst_path = rst_server_path
    eng_data_path = material_server_path
    composite_definitions_path = h5_server_path

    rst_data_source = dpf.DataSources(rst_path)

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.data_sources(rst_data_source)

    eng_data_source = dpf.DataSources()
    eng_data_source.add_file_path(eng_data_path, "EngineeringData")

    composite_definitions_source = dpf.DataSources()
    composite_definitions_source.add_file_path(composite_definitions_path, "CompositeDefinitions")

    material_support_provider = dpf.Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.data_sources(rst_data_source)

    result_info_provider = dpf.Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = eng_data_source
    material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(eng_data_source)

    layup_provider = dpf.Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh_provider.outputs.mesh)
    layup_provider.inputs.data_sources(composite_definitions_source)
    layup_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    layup_provider.run()

    strain_operator = dpf.Operator("EPEL")
    strain_operator.inputs.data_sources(rst_data_source)
    strain_operator.inputs.bool_rotate_to_global(False)

    stress_operator = dpf.Operator("S")
    stress_operator.inputs.data_sources(rst_data_source)
    stress_operator.inputs.bool_rotate_to_global(False)

    rd = get_basic_combined_failure_criterion()
    failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
    failure_evaluator.inputs.configuration(rd.to_json())
    failure_evaluator.inputs.materials_container(material_provider.outputs.materials_container)
    failure_evaluator.inputs.strains(strain_operator.outputs.fields_container)
    failure_evaluator.inputs.stresses(stress_operator.outputs.fields_container)
    failure_evaluator.inputs.mesh(mesh_provider.outputs.mesh)

    minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
    minmax_per_element.inputs.fields_container(failure_evaluator.outputs.fields_container)
    minmax_per_element.inputs.mesh(mesh_provider.outputs.mesh)
    minmax_per_element.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )

    output = minmax_per_element.outputs.field_max()
    value_index = 1
    ######################################################################################
    assert output[value_index].data.size == 4
    assert output[value_index].data[0] == pytest.approx(1.6239472098214285)
    assert output[value_index].data[1] == pytest.approx(1.6239472098214285)
    assert output[value_index].data[2] == pytest.approx(2.248462289571762)
    assert output[value_index].data[3] == pytest.approx(2.248462289571762)
