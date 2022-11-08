from contextlib import contextmanager
from dataclasses import dataclass
import pathlib
from typing import Dict, Generator, List, Optional

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, Field, MeshedRegion, PropertyField
import numpy as np
import pytest

from ansys.dpf.composites.layup_info import (
    ElementInfo,
    ElementInfoProvider,
    get_analysis_ply_info_provider,
    get_element_info_provider,
)
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_material_id,
)

from .helper import CompositeFiles, setup_operators


@dataclass
class FieldInfo:
    field: Field
    layup_info: ElementInfoProvider


@contextmanager
def get_field_info(
    input_field: Field, mesh: MeshedRegion, rst_data_source: DataSources
) -> Generator[FieldInfo, None, None]:
    layup_info = get_element_info_provider(mesh, rst_data_source=rst_data_source)
    with input_field.as_local_field() as local_input_field:
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
    ) as field_info:
        analysis_ply_info_provider = get_analysis_ply_info_provider(
            mesh=setup_result.mesh, name="P1L1__ud_patch ns1"
        )
        with result_field.as_local_field() as local_result_field:
            for element_id in analysis_ply_info_provider.property_field.scoping.ids:
                strain_data = field_info.field.get_entity_data_by_id(element_id)

                element_info = field_info.layup_info.get_element_info(element_id)
                selected_indices = get_selected_indices_by_analysis_ply(
                    analysis_ply_info_provider, element_info
                )
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


@dataclass
class ExpectedOutput:
    n_layers: int
    n_corner_nodes: int
    element_type: int
    # n_spots can be 0 for homogenous solids or
    # if output is only requested on top/bottom of the element
    # otherwise it is 2 or 3 for top/bot or top/bot/mid output
    n_spots: int
    is_layered: bool


def test_all_element_types(dpf_server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data"

    def get_expected_output(
        with_mid: bool, only_top_bot_of_stack: bool
    ) -> Dict[int, ExpectedOutput]:
        if with_mid:
            n_spots_shell = 3
        else:
            n_spots_shell = 2

        if only_top_bot_of_stack:
            n_spots_shell = 0

        if only_top_bot_of_stack:
            n_spots_layered_solid = 0
        else:
            n_spots_layered_solid = 2

        n_spots_homogeneous_solid = 0
        return {
            1: ExpectedOutput(3, 4, 181, n_spots_shell, True),
            2: ExpectedOutput(3, 3, 181, n_spots_shell, True),
            3: ExpectedOutput(3, 4, 281, n_spots_shell, True),
            4: ExpectedOutput(3, 3, 281, n_spots_shell, True),
            10: ExpectedOutput(1, 8, 185, n_spots_homogeneous_solid, False),
            11: ExpectedOutput(1, 6, 185, n_spots_homogeneous_solid, False),
            12: ExpectedOutput(1, 5, 185, n_spots_homogeneous_solid, False),
            13: ExpectedOutput(1, 4, 185, n_spots_homogeneous_solid, False),
            20: ExpectedOutput(1, 8, 186, n_spots_homogeneous_solid, False),
            21: ExpectedOutput(1, 6, 186, n_spots_homogeneous_solid, False),
            22: ExpectedOutput(1, 5, 186, n_spots_homogeneous_solid, False),
            23: ExpectedOutput(1, 4, 186, n_spots_homogeneous_solid, False),
            30: ExpectedOutput(3, 8, 185, n_spots_layered_solid, True),
            31: ExpectedOutput(3, 6, 185, n_spots_layered_solid, True),
            40: ExpectedOutput(3, 8, 186, n_spots_layered_solid, True),
            41: ExpectedOutput(3, 6, 186, n_spots_layered_solid, True),
            50: ExpectedOutput(3, 8, 190, n_spots_layered_solid, True),
            51: ExpectedOutput(3, 6, 190, n_spots_layered_solid, True),
        }

    def check_output(rst_file, expected_output):
        rst_path = TEST_DATA_ROOT_DIR / "all_element_types" / rst_file
        rst_path = dpf.upload_file_in_tmp_folder(rst_path, server=dpf_server)

        rst_data_source = dpf.DataSources(rst_path)

        mesh_provider = dpf.Operator("MeshProvider")
        mesh_provider.inputs.data_sources(rst_data_source)
        mesh: MeshedRegion = mesh_provider.outputs.mesh()

        # Mock the info that gets added in the layup provider
        # All the layered elements have a layered section with three layers (materials 1,2,1)
        material_property_field = PropertyField()
        layer_indices_property_field = PropertyField()
        element_ids = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 40, 41, 50, 51]
        layered_element_ids = [1, 2, 3, 4, 30, 31, 40, 41, 50, 51]
        for layered_element_id in layered_element_ids:
            material_property_field.append([1, 2, 1], layered_element_id)
            layer_indices_property_field.append([3, 0, 1, 2], layered_element_id)

        mesh.set_property_field("element_layered_material_ids", material_property_field)
        mesh.set_property_field("element_layer_indices", layer_indices_property_field)

        strain_operator = dpf.Operator("EPEL")
        strain_operator.inputs.data_sources(rst_data_source)
        strain_operator.inputs.bool_rotate_to_global(False)

        fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)
        field = fields_container[0]

        with get_field_info(
            input_field=field,
            mesh=mesh,
            rst_data_source=rst_data_source,
        ) as field_info:
            for element_id in element_ids:
                element_info: ElementInfo = field_info.layup_info.get_element_info(element_id)
                assert element_info.element_type == expected_output[element_id].element_type
                assert element_info.is_layered == expected_output[element_id].is_layered
                if element_info.is_layered:
                    assert list(element_info.material_ids) == [1, 2, 1]
                assert element_info.n_spots == expected_output[element_id].n_spots, str(
                    element_info
                )
                assert (
                    element_info.n_corner_nodes == expected_output[element_id].n_corner_nodes
                ), str(element_info)

                field: Field = field_info.field
                entity_data = field.get_entity_data_by_id(element_id)
                num_elementary_data = entity_data.shape[0]

                if element_info.n_spots == 0:
                    if element_info.is_shell:
                        # Shell with only bottom-top-of-stack output
                        assert num_elementary_data == 2 * element_info.n_corner_nodes
                    else:
                        # Solid with only bottom-top-of-stack output or homogeneous solid
                        assert num_elementary_data == element_info.n_corner_nodes
                else:
                    if element_info.is_shell:
                        corner_nodes_per_layer = element_info.n_corner_nodes
                    else:
                        corner_nodes_per_layer = element_info.n_corner_nodes / 2
                    assert (
                        num_elementary_data
                        == corner_nodes_per_layer * element_info.n_spots * element_info.n_layers
                    )

    check_output(
        "model_with_all_element_types_all_except_mid_output.rst",
        get_expected_output(with_mid=False, only_top_bot_of_stack=False),
    )

    check_output(
        "model_with_all_element_types_all_output.rst",
        get_expected_output(with_mid=True, only_top_bot_of_stack=False),
    )

    check_output(
        "model_with_all_element_types_minimal_output.rst",
        get_expected_output(with_mid=True, only_top_bot_of_stack=True),
    )
