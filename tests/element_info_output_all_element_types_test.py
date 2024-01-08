from collections.abc import Collection
from dataclasses import dataclass
import pathlib

import ansys.dpf.core as dpf
from ansys.dpf.core import Field, MeshedRegion, PropertyField
import pytest

from ansys.dpf.composites.constants import Spot
from ansys.dpf.composites.layup_info import ElementInfo, get_element_info_provider
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_dpf_material_ids,
)
from ansys.dpf.composites.server_helpers import upload_file_to_unique_tmp_folder


@dataclass(frozen=True)
class ExpectedOutput:
    n_layers: int
    n_corner_nodes: int
    element_type: int
    # n_spots can be 0 for homogeneous solids or
    # if output is only requested on top/bottom of the element
    # otherwise it is 2 or 3 for top/bot or top/bot/mid output
    n_spots: int
    is_layered: bool


@dataclass(frozen=True)
class ElementIds:
    all: Collection[int]
    layered: Collection[int]
    non_layered: Collection[int]


def get_element_ids() -> ElementIds:
    """
    Element ids in the "all_element_types" rst files
    """
    layered_element_ids = [1, 2, 3, 4, 30, 31, 40, 41, 50, 51]
    element_ids = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23, 24, 30, 31, 40, 41, 50, 51]
    non_layered_element_ids = set(element_ids).difference(set(layered_element_ids))

    return ElementIds(element_ids, layered_element_ids, non_layered_element_ids)


def get_layup_property_fields():
    """
    Helper function to get lay-up information for the all_element_types*.rst
    files without a lay-up definition file.
    """
    # Mock the info that gets added in the lay-up provider
    # All the layered elements have a layered section with three layers (materials 1,2,1)
    material_property_field = PropertyField()
    layer_indices_property_field = PropertyField()

    # The rst file contains all types of elements
    # Please check the *.dat files in dpf_composites/test_data/model_with_all_element_types
    # for the definition of the elements
    for layered_element_id in get_element_ids().layered:
        material_property_field.append([1, 2, 1], layered_element_id)
        layer_indices_property_field.append([3, 0, 1, 2], layered_element_id)
    return material_property_field, layer_indices_property_field


def test_all_element_types(dpf_server):
    """
    Check ElementInfo objects for all supported element types. Check that num_elementary data
    of the strain output is consistent with the number_elementary_data computed for element_info
    """
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data"

    def get_expected_output(
        with_mid: bool, only_top_bot_of_stack: bool
    ) -> dict[int, ExpectedOutput]:
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
            24: ExpectedOutput(1, 4, 187, n_spots_homogeneous_solid, False),
            30: ExpectedOutput(3, 8, 185, n_spots_layered_solid, True),
            31: ExpectedOutput(3, 6, 185, n_spots_layered_solid, True),
            40: ExpectedOutput(3, 8, 186, n_spots_layered_solid, True),
            41: ExpectedOutput(3, 6, 186, n_spots_layered_solid, True),
            50: ExpectedOutput(3, 8, 190, n_spots_layered_solid, True),
            51: ExpectedOutput(3, 6, 190, n_spots_layered_solid, True),
        }

    def check_output(rst_file, expected_output):
        rst_path = TEST_DATA_ROOT_DIR / "all_element_types" / rst_file
        if not dpf_server.local_server:
            rst_path = upload_file_to_unique_tmp_folder(rst_path, server=dpf_server)

        rst_data_source = dpf.DataSources(rst_path)

        mesh_provider = dpf.Operator("MeshProvider")
        mesh_provider.inputs.data_sources(rst_data_source)
        mesh: MeshedRegion = mesh_provider.outputs.mesh()

        material_property_field, layer_indices_property_field = get_layup_property_fields()
        mesh.set_property_field("element_layered_material_ids", material_property_field)
        mesh.set_property_field("element_layer_indices", layer_indices_property_field)

        strain_operator = dpf.operators.result.elastic_strain()
        strain_operator.inputs.data_sources(rst_data_source)
        strain_operator.inputs.bool_rotate_to_global(False)

        fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)
        field = fields_container[0]
        element_info_provider = get_element_info_provider(mesh, rst_data_source)
        with field.as_local_field() as local_field:
            for element_id in get_element_ids().all:
                element_info: ElementInfo = element_info_provider.get_element_info(element_id)
                assert element_info.element_type == expected_output[element_id].element_type
                assert element_info.is_layered == expected_output[element_id].is_layered
                if element_info.is_layered:
                    assert list(element_info.dpf_material_ids) == [1, 2, 1]
                assert element_info.n_spots == expected_output[element_id].n_spots, str(
                    element_info
                )
                assert (
                    element_info.n_corner_nodes == expected_output[element_id].n_corner_nodes
                ), str(element_info)

                field: Field = local_field
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


def test_document_error_cases_indices(dpf_server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data"

    def get_layup_info_for_rst(rst_file):
        rst_path = TEST_DATA_ROOT_DIR / "all_element_types" / rst_file

        if not dpf_server.local_server:
            rst_path = upload_file_to_unique_tmp_folder(rst_path, server=dpf_server)

        rst_data_source = dpf.DataSources(rst_path)

        mesh_provider = dpf.Operator("MeshProvider")
        mesh_provider.inputs.data_sources(rst_data_source)
        mesh: MeshedRegion = mesh_provider.outputs.mesh()

        with pytest.raises(RuntimeError) as exc_info:
            layup_info = get_element_info_provider(
                mesh, stream_provider_or_data_source=rst_data_source
            )
        assert str(exc_info.value).startswith("Missing property field in mesh")
        material_property_field, layer_indices_property_field = get_layup_property_fields()
        mesh.set_property_field("element_layered_material_ids", material_property_field)
        mesh.set_property_field("element_layer_indices", layer_indices_property_field)
        return get_element_info_provider(mesh, stream_provider_or_data_source=rst_data_source)

    layup_info = get_layup_info_for_rst("model_with_all_element_types_minimal_output.rst")

    for element_id in get_element_ids().layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[1])
        assert str(exc_info.value).startswith(
            "Computation of indices is not supported for elements with no spots"
        )

    for element_id in get_element_ids().non_layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[1])
        assert str(exc_info.value).startswith(
            "Computation of indices is not supported for non-layered elements."
        )

    layup_info = get_layup_info_for_rst("model_with_all_element_types_all_output.rst")

    for element_id in get_element_ids().non_layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[1])
        assert str(exc_info.value).startswith(
            "Computation of indices is not supported for non-layered elements."
        )

    for element_id in get_element_ids().layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[3])
        assert str(exc_info.value).startswith(
            "Layer index 3 is greater or equal to the number of layers: 3"
        )

    for element_id in get_element_ids().layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[1], nodes=[4])
        assert str(exc_info.value).startswith(
            "Corner node index 4 is greater or equal to the number of corner nodes"
        )

    # Try to get non-existing dpf_material_id
    element_info: ElementInfo = layup_info.get_element_info(1)
    selected_indices = get_selected_indices_by_dpf_material_ids(element_info, [5])
    assert len(selected_indices) == 0

    layup_info = get_layup_info_for_rst("model_with_all_element_types_all_except_mid_output.rst")

    for element_id in get_element_ids().layered:
        with pytest.raises(RuntimeError) as exc_info:
            element_info: ElementInfo = layup_info.get_element_info(element_id)
            get_selected_indices(element_info, layers=[1], nodes=[1], spots=[Spot.MIDDLE])
        assert str(exc_info.value).startswith(
            "Spot index 2 is greater or equal to the number of spots"
        )
