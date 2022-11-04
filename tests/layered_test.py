from contextlib import contextmanager
from dataclasses import dataclass
import pathlib
from typing import Any, List, Optional

import ansys.dpf.core as dpf
import numpy as np
import pytest

from ansys.dpf.composites.layup_info import ElementInfoProvider, get_analysis_ply, get_layup_info
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_material_id,
)

from .helper import CompositeFiles, setup_operators


@dataclass
class FieldInfo:
    field: Any
    layup_info: ElementInfoProvider


@contextmanager
def get_field_info(input_field, mesh, rst_data_source):
    with input_field.as_local_field() as local_input_field:
        with get_layup_info(mesh, rst_data_source=rst_data_source) as layup_info:
            yield FieldInfo(field=local_input_field, layup_info=layup_info)


def get_result_field(
    field_info: FieldInfo,
    layers: Optional[List[int]] = None,
    corner_nodes: Optional[List[int]] = None,
    spots: Optional[List[int]] = None,
    scope: Optional[List[int]] = None,
    material_id: Optional[int] = None,
):
    """
    Convenience function to get a filtered field. Getting the strain data is
    not optimized using data_pointers. This function is not very generic but should
    capture some common use cases that users use.
    Note: If a material_id are specified, corner_nodes, spots and layers are ignored.
    """
    component = 0
    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
    with result_field.as_local_field() as local_result_field:
        if scope is None:
            scope = field_info.field.scoping.ids
        for element_id in scope:
            strain_data = field_info.field.get_entity_data_by_id(element_id)
            element_info = field_info.layup_info.get_element_info(element_id)
            if element_info.is_layered:
                if material_id:
                    selected_indices = get_selected_indices_by_material_id(
                        element_info, material_id
                    )
                else:
                    selected_indices = get_selected_indices(
                        element_info, layers=layers, corner_nodes=corner_nodes, spots=spots
                    )

                value = strain_data[selected_indices][:, component]
                local_result_field.append(value, element_id)
            else:
                local_result_field.append(strain_data[selected_indices, component], element_id)
    return result_field


def get_data_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = TEST_DATA_ROOT_DIR / "shell.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return CompositeFiles(rst_path=rst_path, h5_path=h5_path, material_path=material_path)


def test_filter_by_layer_spot_and_corner_node_index(dpf_server):
    files = get_data_files()
    setup_result = setup_operators(dpf_server, files)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        # Test single value output
        result_field = get_result_field(
            field_info, layers=[5], corner_nodes=[3], spots=[2], scope=[1]
        )
        assert result_field.get_entity_data_by_id(1) == pytest.approx(3.05458950e-03)

        # Test layer output for layer and spot selection (nodes of a given spot+layer)
        result_field = get_result_field(field_info, layers=[0], spots=[2], scope=[1])
        assert result_field.get_entity_data_by_id(1) == pytest.approx(
            setup_result.field.get_entity_data_by_id(1)[8:12, 0]
        )

        # Test filter by material
        # Material 2 is present in layer 1,2 and 4
        result_field_by_mat = get_result_field(field_info, material_id=2)
        result_field_layer = get_result_field(field_info, layers=[1, 2, 4])

        assert result_field_by_mat.get_entity_data_by_id(1) == pytest.approx(
            result_field_layer.get_entity_data_by_id(1)
        )


def test_filter_by_global_ply(dpf_server):
    files = get_data_files()

    setup_result = setup_operators(dpf_server, files)

    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info, get_analysis_ply(
        mesh=setup_result.mesh, name="P1L1__ud_patch ns1"
    ) as analysis_ply:
        with result_field.as_local_field() as local_result_field:
            for element_id in analysis_ply.scoping.ids:
                strain_data = field_info.field.get_entity_data_by_id(element_id)

                layer_index = analysis_ply.get_entity_data_by_id(element_id)
                element_info = field_info.layup_info.get_element_info(element_id)

                selected_indices = get_selected_indices(element_info, layers=[layer_index])
                component = 0
                value = strain_data[selected_indices][:, component]

                local_result_field.append(value, element_id)

    # Ply is only present in element 1 and 2
    assert list(result_field.scoping.ids) == [1, 2]
    # Global Ply is layer 2
    assert result_field.get_entity_data_by_id(1) == pytest.approx(
        setup_result.field.get_entity_data_by_id(1)[12:24, 0]
    )

    # Global Ply is layer 2
    assert result_field.get_entity_data_by_id(2) == pytest.approx(
        setup_result.field.get_entity_data_by_id(2)[12:24, 0]
    )


def test_material_properties(dpf_server):
    """
    Test evaluation of material properties to compute a user defined failure criterion
    Properties are precomputed. Needs to be improves. The test documents the current status
    """
    files = get_data_files()

    setup_result = setup_operators(dpf_server, files)

    properties = []
    # Number of materials is hardcoded. Should be determined from the material support
    for id in [1, 2, 3, 4]:
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
