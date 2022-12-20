import os
import pathlib

import ansys.dpf.core as dpf

from ansys.dpf.composites import MaterialProperty
from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope, LayerProperty
from ansys.dpf.composites.example_helper.example_helper import upload_composite_files_to_server
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStrainCriterion

from .helper import ContinuousFiberCompositesFiles, Timer


def check_performance(timer, last_measured_performance, performance_factor=1.1):
    assert timer.get_runtime_without_first_step() < last_measured_performance * performance_factor
    assert timer.get_runtime_without_first_step() > last_measured_performance / performance_factor


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


def get_ger_data_files():
    ger_path = (
        pathlib.Path("D:\\")
        / "ANSYSDev"
        / "additional_model_data"
        / "ger89"
        / "ger89_files"
        / "dp0"
    )

    rst_path = ger_path / "SYS-1" / "MECH" / "file.rst"
    h5_path = ger_path / "ACP-Pre" / "ACP" / "ACPCompositeDefinitions.h5"
    material_path = ger_path / "SYS-1" / "MECH" / "MatML.xml"
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

    composite_model = CompositeModel(files)
    timer.add("After Setup model")

    combined_failure_criterion = CombinedFailureCriterion(
        "max strain & max stress", failure_criteria=[MaxStrainCriterion(), MaxStrainCriterion()]
    )

    failure_output = composite_model.evaluate_failure_criteria(
        combined_criteria=combined_failure_criterion,
        composite_scope=CompositeScope(),
    )

    properyt_dict = composite_model.get_constant_property_dict(
        [MaterialProperty.Strain_Limits_eXt, MaterialProperty.Hill_Yield_Criterion_R12]
    )

    timer.add("After get property dict")

    for element_id in composite_model.mesh.elements.scoping.ids:
        element_info = composite_model.get_element_info(element_id)

    timer.add("After getting element_info")

    for element_id in composite_model.mesh.elements.scoping.ids:
        composite_model.get_layer_property(LayerProperty.shear_angles, element_id)
    timer.add("After getting property")

    timer.summary()
