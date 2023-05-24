from typing import List, Optional

import ansys.dpf.core as dpf
from ansys.dpf.core import Field
import numpy as np
import pytest

from ansys.dpf.composites.constants import Spot
from ansys.dpf.composites.layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfoProvider,
    get_element_info_provider,
)
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)

from .helper import get_basic_shell_files, setup_operators


def get_result_field(
    element_info_provider: ElementInfoProvider,
    input_field: Field,
    layers: Optional[List[int]] = None,
    corner_nodes: Optional[List[int]] = None,
    spots: Optional[List[Spot]] = None,
    element_ids: Optional[List[int]] = None,
    dpf_material_id: Optional[np.int64] = None,
):
    """
    Convenience function to get a filtered field. Getting the strain data is
    not optimized using data_pointers. This function is not very generic but should
    capture some common use cases that users use.
    Note: If a dpf_material_id are specified, corner_nodes, spots and layers are ignored.
    """
    component = 0
    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
    with input_field.as_local_field() as input_local_field:
        with result_field.as_local_field() as local_result_field:
            if element_ids is None:
                element_ids = input_local_field.scoping.ids
            for element_id in element_ids:
                strain_data = input_local_field.get_entity_data_by_id(element_id)
                element_info = element_info_provider.get_element_info(element_id)
                assert element_info is not None
                if element_info.is_layered:
                    if dpf_material_id:
                        selected_indices = get_selected_indices_by_dpf_material_ids(
                            element_info, [dpf_material_id]
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

    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )
    # Test single value output
    result_field = get_result_field(
        element_info_provider=element_info_provider,
        input_field=setup_result.field,
        layers=[5],
        corner_nodes=[3],
        spots=[Spot.MIDDLE],
        element_ids=[1],
    )
    assert result_field.get_entity_data_by_id(1) == pytest.approx(3.05458950e-03)

    # Test layer output for layer and spot selection (nodes of a given spot+layer)
    result_field = get_result_field(
        element_info_provider=element_info_provider,
        input_field=setup_result.field,
        layers=[0],
        spots=[Spot.MIDDLE],
        element_ids=[1],
    )
    assert result_field.get_entity_data_by_id(1) == pytest.approx(
        setup_result.field.get_entity_data_by_id(1)[8:12, 0]
    )

    mat_id_of_layers = element_info_provider.get_element_info(1).dpf_material_ids

    layers_with_same_material = [1, 2, 4]
    # Make sure all the layers have the same material
    assert len({mat_id_of_layers[mat_id] for mat_id in layers_with_same_material}) == 1
    # Test filter by material
    # Material 2 is present in layer 1,2 and 4
    result_field_by_mat = get_result_field(
        element_info_provider=element_info_provider,
        input_field=setup_result.field,
        dpf_material_id=mat_id_of_layers[layers_with_same_material[0]],
    )
    result_field_layer = get_result_field(
        element_info_provider=element_info_provider,
        input_field=setup_result.field,
        layers=layers_with_same_material,
    )

    assert result_field_by_mat.get_entity_data_by_id(1) == pytest.approx(
        result_field_layer.get_entity_data_by_id(1)
    )


def test_filter_by_global_ply(dpf_server):
    files = get_basic_shell_files()

    setup_result = setup_operators(dpf_server, files)

    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )

    with setup_result.field.as_local_field() as local_field:
        analysis_ply_info_provider = AnalysisPlyInfoProvider(
            mesh=setup_result.mesh, name="P1L1__ud_patch ns1"
        )
        with result_field.as_local_field() as local_result_field:
            for element_id in analysis_ply_info_provider.property_field.scoping.ids:
                strain_data = local_field.get_entity_data_by_id(element_id)

                element_info = element_info_provider.get_element_info(element_id)
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
    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )

    # Try to get non existing element
    with pytest.raises(RuntimeError) as exc_info:
        element_info = element_info_provider.get_element_info(1000)
    assert str(exc_info.value).startswith("Could not determine element properties")


def test_access_to_invalid_analysis_ply(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )
    # try to get non existing analysis ply
    with pytest.raises(RuntimeError) as exc_info:
        analysis_ply_info_provider = AnalysisPlyInfoProvider(
            mesh=setup_result.mesh, name="notexisting"
        )
    assert str(exc_info.value).startswith("Analysis ply is not available")

    # try to get element that is not part of analysis ply
    analysis_ply_info_provider = AnalysisPlyInfoProvider(
        mesh=setup_result.mesh, name="P1L1__ud_patch ns1"
    )
    with pytest.raises(RuntimeError) as exc_info:
        element_info = element_info_provider.get_element_info(4)
        selected_indices = get_selected_indices_by_analysis_ply(
            analysis_ply_info_provider, element_info
        )

    assert str(exc_info.value) == "Analysis Ply 'P1L1__ud_patch ns1' is not part of element 4"
