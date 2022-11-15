import ansys.dpf.core as dpf
import numpy as np
import pytest

from ansys.dpf.composites.select_indices import get_selected_indices

from .helper import get_basic_shell_files, get_field_info, setup_operators


def test_material_properties(dpf_server):
    """
    Test evaluation of material properties to compute a user defined failure criterion
    Properties are precomputed. Needs to be improve and be properly documented.
    The test documents the current status
    """
    files = get_basic_shell_files()

    setup_result = setup_operators(dpf_server, files)

    properties = []
    # Number of materials is hardcoded. Should be determined from the material support
    for id in [1, 2, 3, 4]:
        # Check EngineeringDataDefinitions.cpp for available properties
        property_name = "strain_tensile_x_direction"
        material_property_field = dpf.Operator("eng_data::ans_mat_property_field_provider")
        material_property_field.inputs.materials_container(setup_result.material_provider)
        material_property_field.inputs.dpf_mat_id(id)
        material_property_field.inputs.property_name(property_name)
        result_info_provider = dpf.Operator("ResultInfoProvider")
        result_info_provider.inputs.data_sources(setup_result.rst_data_source)
        material_property_field.inputs.unit_system_or_result_info(result_info_provider)
        properties.append(
            material_property_field.get_output(output_type=dpf.types.fields_container)[0].data[0]
        )

    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        with result_field.as_local_field() as local_result_field:
            component = 0

            for element_id in field_info.field.scoping.ids:
                strain_data = field_info.field.get_entity_data_by_id(element_id)
                element_info = field_info.layup_info.get_element_info(element_id)
                layer_data = []
                for layer_index, material_id in enumerate(element_info.material_ids):
                    ext = properties[material_id - 1]
                    selected_indices = get_selected_indices(element_info, layers=[layer_index])
                    # Max strain criteria in x direction
                    value = strain_data[selected_indices][:, component]
                    if ext > 0:
                        layer_data.append(np.max(value / ext))

                local_result_field.append([np.max(layer_data)], element_id)

    assert list(result_field.scoping.ids) == [1, 2, 3, 4]

    assert result_field.get_entity_data_by_id(1) == pytest.approx([1.3871777438275192])
