import ansys.dpf.core as dpf
import numpy as np
import pytest

from ansys.dpf.composites.data_sources import get_composites_data_sources
from ansys.dpf.composites.example_helper import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.layup_info import (
    AnalysisPlyInfoProvider,
    get_all_analysis_ply_names,
    get_analysis_ply_index_to_name_map,
    get_dpf_material_id_by_analyis_ply_map,
    get_element_info_provider,
)
from ansys.dpf.composites.layup_info.material_operators import get_material_operators
from ansys.dpf.composites.layup_info.material_properties import (
    MaterialProperty,
    get_constant_property_dict,
)
from ansys.dpf.composites.select_indices import get_selected_indices

from .helper import get_basic_shell_files, setup_operators


def test_get_analysis_ply_material_id_map(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    material_map = get_dpf_material_id_by_analyis_ply_map(
        setup_result.mesh, setup_result.streams_provider
    )

    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )
    for analyis_ply_name in get_all_analysis_ply_names(setup_result.mesh):
        analysis_ply_info_provider = AnalysisPlyInfoProvider(setup_result.mesh, analyis_ply_name)
        for element_id in analysis_ply_info_provider.property_field.scoping.ids:
            element_info = element_info_provider.get_element_info(element_id)
            layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(element_id)
            assert material_map[analyis_ply_name] == element_info.dpf_material_ids[layer_index]


def test_get_analysis_ply_index_to_name_map(dpf_server):
    files = get_basic_shell_files()
    setup_result = setup_operators(dpf_server, files)

    analysis_ply_map = get_analysis_ply_index_to_name_map(setup_result.mesh)

    assert analysis_ply_map == {
        0: "P1L1__woven_45",
        1: "P1L1__ud_patch ns1",
        2: "P1L1__ud",
        3: "P1L1__core",
        4: "P1L1__ud.2",
        5: "P1L1__woven_45.2",
    }


def test_material_properties(dpf_server):
    """
    Test evaluation of material properties to compute a user defined failure criterion
    """
    files = get_basic_shell_files()

    setup_result = setup_operators(dpf_server, files)

    material_property = MaterialProperty.Strain_Limits_eXt

    property_dict = get_constant_property_dict(
        material_properties=[material_property],
        materials_provider=setup_result.material_provider,
        data_source_or_streams_provider=setup_result.streams_provider,
        mesh=setup_result.mesh,
    )
    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

    element_info_provider = get_element_info_provider(
        setup_result.mesh, setup_result.streams_provider
    )
    with setup_result.field.as_local_field() as local_input_field:
        with result_field.as_local_field() as local_result_field:
            component = 0

            for element_id in local_input_field.scoping.ids:
                strain_data = local_input_field.get_entity_data_by_id(element_id)
                element_info = element_info_provider.get_element_info(element_id)
                layer_data = []
                for layer_index, dpf_material_id in enumerate(element_info.dpf_material_ids):
                    ext = property_dict[dpf_material_id][material_property]
                    selected_indices = get_selected_indices(element_info, layers=[layer_index])
                    # Max strain criteria in x direction
                    value = strain_data[selected_indices][:, component]
                    if ext > 0:
                        layer_data.append(np.max(value / ext))

                local_result_field.append([np.max(layer_data)], element_id)

    assert list(result_field.scoping.ids) == [1, 2, 3, 4]

    assert result_field.get_entity_data_by_id(1) == pytest.approx([1.3871777438275192])


def test_material_properties_fails_with_error_mesh_has_no_layup_info(dpf_server):

    files = get_basic_shell_files()
    if not dpf_server.local_server:
        files = upload_continuous_fiber_composite_files_to_server(
            data_files=files, server=dpf_server
        )

    data_sources = get_composites_data_sources(files)

    streams_provider = dpf.operators.metadata.streams_provider()
    streams_provider.inputs.data_sources.connect(data_sources.rst)

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.streams_container(streams_provider)
    mesh = mesh_provider.outputs.mesh()

    material_operators = get_material_operators(
        rst_data_source=data_sources.rst, engineering_data_source=data_sources.rst
    )

    material_property = MaterialProperty.Stress_Limits_Xt

    with pytest.raises(RuntimeError) as exc_info:
        get_constant_property_dict(
            material_properties=[material_property],
            materials_provider=material_operators.material_provider,
            data_source_or_streams_provider=data_sources.rst,
            mesh=mesh,
        )
    assert "Please call add_layup_info_to_mesh" in str(exc_info.value)
