import os
import pathlib

import ansys.dpf.core as dpf
import pytest

from ansys.dpf.composites import MaterialProperty
from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.enums import LayerProperty
from ansys.dpf.composites.example_helper.example_helper import upload_composite_files_to_server
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStrainCriterion

from .helper import ContinuousFiberCompositesFiles, Timer


def get_data_files():
    # Using lightweight data for unit tests. Replace by get_ger_data_data_files
    # for actual performance tests
    # return get_ger_data_files()
    return get_dummy_data_files()


def get_dummy_data_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    return ContinuousFiberCompositesFiles(
        rst=rst_path, composite_definitions=h5_path, engineering_data=material_path
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
    files = upload_composite_files_to_server(data_files=files, server=dpf_server)
    timer.add("After Upload files")

    composite_model = CompositeModel(files, server=dpf_server)
    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStrainCriterion(), MaxStrainCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criteria=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )

    assert failure_output.get_field({"failure_label": 0}).data == pytest.approx(
        [111.0, 121.0, 140, 140]
    )

    properyt_dict = composite_model.get_constant_property_dict(
        [MaterialProperty.Strain_Limits_eXt, MaterialProperty.Hill_Yield_Criterion_R12]
    )

    assert properyt_dict[2][MaterialProperty.Strain_Limits_eXt] == pytest.approx(0.0167)

    timer.add("After get property dict")

    element_infos = [
        composite_model.get_element_info(element_id)
        for element_id in composite_model.mesh.elements.scoping.ids
    ]

    assert element_infos[0].element_type == 181

    timer.add("After getting element_info")

    expected_values = {
        LayerProperty.shear_angles: [0, 0, 0, 0, 0, 0],
        LayerProperty.angles: [45, 0, 0, 0, 0, 45],
        LayerProperty.thicknesses: [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025],
    }
    element_id = 1
    for layer_property, value in expected_values.items():
        assert composite_model.get_layer_property(layer_property, element_id) == pytest.approx(
            value
        )

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
