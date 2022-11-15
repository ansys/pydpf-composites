from typing import List, Optional

import ansys.dpf.core as dpf
import pytest

from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_material_ids,
)

from .helper import FieldInfo, get_basic_shell_files, get_field_info, setup_operators


def get_result_field(
    field_info: FieldInfo,
    layers: Optional[List[int]] = None,
    corner_nodes: Optional[List[int]] = None,
    spots: Optional[List[int]] = None,
    element_ids: Optional[List[int]] = None,
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
        if element_ids is None:
            element_ids = field_info.field.scoping.ids
        for element_id in element_ids:
            strain_data = field_info.field.get_entity_data_by_id(element_id)
            element_info = field_info.layup_info.get_element_info(element_id)
            if element_info.is_layered:
                if material_id:
                    selected_indices = get_selected_indices_by_material_ids(
                        element_info, [material_id]
                    )
                else:
                    selected_indices = get_selected_indices(
                        element_info, layers=layers, nodes=corner_nodes, spots=spots
                    )

                value = strain_data[selected_indices][:, component]
                local_result_field.append(value, element_id)
            else:
                local_result_field.append(strain_data[selected_indices, component], element_id)
    return result_field


def test_filter_by_layer_spot_and_corner_node_index(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        # Test single value output
        result_field = get_result_field(
            field_info, layers=[5], corner_nodes=[3], spots=[2], element_ids=[1]
        )
        assert result_field.get_entity_data_by_id(1) == pytest.approx(3.05458950e-03)

        # Test layer output for layer and spot selection (nodes of a given spot+layer)
        result_field = get_result_field(field_info, layers=[0], spots=[2], element_ids=[1])
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
    files = get_basic_shell_files()

    setup_result = setup_operators(dpf_server, files)

    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        analysis_ply_info_provider = AnalysisPlyInfoProvider(
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


def test_access_to_invalid_element(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        # Try to get non existing element
        with pytest.raises(RuntimeError) as exc_info:
            element_info = field_info.layup_info.get_element_info(1000)
        assert str(exc_info.value).startswith("Could not determine element properties")


def test_access_to_invalid_analysis_ply(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    with get_field_info(
        input_field=setup_result.field,
        mesh=setup_result.mesh,
        rst_data_source=setup_result.rst_data_source,
    ) as field_info:
        # try to get non existing anlysis ply
        with pytest.raises(RuntimeError) as exc_info:

            analysis_ply_info_provider = AnalysisPlyInfoProvider(
                mesh=setup_result.mesh, name="notexisting"
            )
        assert str(exc_info.value).startswith("Analysis Ply not available")

        # try to get element that is not part of analysis ply
        analysis_ply_info_provider = AnalysisPlyInfoProvider(
            mesh=setup_result.mesh, name="P1L1__ud_patch ns1"
        )
        with pytest.raises(RuntimeError) as exc_info:
            element_info = field_info.layup_info.get_element_info(4)
            selected_indices = get_selected_indices_by_analysis_ply(
                analysis_ply_info_provider, element_info
            )

        assert str(exc_info.value) == "Analysis Ply 'P1L1__ud_patch ns1' is not part of element 4"
