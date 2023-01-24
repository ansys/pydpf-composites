import os
import pathlib

import ansys.dpf.core as dpf
import numpy as np
import pytest

from ansys.dpf.composites import MaterialProperty, get_constant_property_dict
from ansys.dpf.composites.add_layup_info_to_mesh import add_layup_info_to_mesh
from ansys.dpf.composites.composite_data_sources import (
    CompositeDefinitionFiles,
    get_composites_data_sources,
)
from ansys.dpf.composites.example_helper import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.indexer import _FieldIndexerWithDataPointer
from ansys.dpf.composites.layup_info import LayupPropertiesProvider, get_element_info_provider
from ansys.dpf.composites.material_setup import get_material_operators

from .helper import ContinuousFiberCompositesFiles, Timer, setup_operators


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
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
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
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )


def get_test_data(dpf_server):
    files = get_data_files()
    rst_path = dpf.upload_file_in_tmp_folder(files.rst, server=dpf_server)

    rst_data_source = dpf.DataSources(rst_path)

    strain_operator = dpf.operators.result.elastic_strain()
    strain_operator.inputs.data_sources(rst_data_source)
    strain_operator.inputs.bool_rotate_to_global(False)

    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)
    field = fields_container[0]
    return field


def get_generated_test_data(server, n_components=6):
    n_entities = 10000
    n_layers_times_nodes_times_integration_points = 10 * 4 * 3

    field = dpf.fields_factory.create_vector_field(
        num_entities=0, server=server, num_comp=n_components
    )
    with field.as_local_field() as f:
        for id in range(1, n_entities + 1):
            f.append(np.ones(n_layers_times_nodes_times_integration_points * n_components), id)

    return field


def test_performance_data_pointer(dpf_server):
    timer = Timer()

    n_components = 6
    field = get_generated_test_data(dpf_server, n_components=n_components)

    timer.add("read data")

    indices = np.ones(np.max(field.scoping.ids) + 1, dtype=int) * -1
    timer.add("Indices setup")

    indices[field.scoping.ids] = np.arange(len(field.scoping.ids))
    timer.add("Indices setup 2")

    data = field.data
    timer.add("get numpy data")

    data_pointer = field._data_pointer // n_components
    timer.add("data pointer division")
    data_pointer_with_end = np.append(data_pointer, len(data))
    timer.add("data pointer with end")
    max_per_element = np.zeros(len(field.scoping.ids))
    for element_idx, element_id in enumerate(field.scoping.ids):
        idx = indices[element_id]
        max_per_element[element_idx] = np.max(
            data[data_pointer_with_end[idx] : data_pointer_with_end[idx + 1], 0]
        )

    timer.add("loop")

    timer.summary()


def test_performance_by_index(dpf_server):
    timer = Timer()

    field = get_generated_test_data(dpf_server)
    timer.add("read data")

    with field.as_local_field() as local_field:
        timer.add("local_field")
        max_per_element = np.zeros(len(local_field.scoping.ids))
        timer.add("allocate")

        for element_idx, element_id in enumerate(local_field.scoping.ids):
            max_per_element[element_idx] = np.max(local_field.get_entity_data(element_idx)[:, 0])

        timer.add("loop")
    timer.add("after local field")

    timer.summary()


def test_performance_by_id(dpf_server):
    timer = Timer()

    field = get_generated_test_data(dpf_server)
    timer.add("read data")

    with field.as_local_field() as local_field:
        timer.add("local_field")
        max_per_element = np.zeros(len(local_field.scoping.ids))
        timer.add("allocate")

        for element_idx, element_id in enumerate(local_field.scoping.ids):
            max_per_element[element_idx] = np.max(
                local_field.get_entity_data_by_id(element_id)[:, 0]
            )

        timer.add("loop")
    timer.add("after local field")

    timer.summary()


def test_performance_element_info(dpf_server):
    timer = Timer()

    files = get_data_files()
    setup_result = setup_operators(dpf_server, files)
    timer.add("read data")

    # This is currently slow because
    # getting the keyoptions is slow.
    # We could implement the option to pass keyoptions directly if
    # they are known
    layup_info = get_element_info_provider(
        setup_result.mesh,
        stream_provider_or_data_source=setup_result.streams_provider,
        no_bounds_checks=True,
    )
    timer.add("layup info")
    scope = setup_result.field.scoping.ids
    timer.add("scope")
    for element_id in scope:
        layup_info.get_element_info(element_id)

    timer.add("loop")
    timer.add("after local field")

    timer.summary()


def test_performance_layup_properties(dpf_server):
    timer = Timer()

    files = get_data_files()
    setup_result = setup_operators(dpf_server, files)
    timer.add("read data")

    layup_info = LayupPropertiesProvider(
        layup_provider=setup_result.layup_provider, mesh=setup_result.mesh
    )

    timer.add("layup info")
    scope = setup_result.field.scoping.ids
    timer.add("scope")
    for element_id in scope:
        layup_info.get_layer_thicknesses(element_id)
        layup_info.get_layer_angles(element_id)
        layup_info.get_layer_shear_angles(element_id)
        layup_info.get_element_laminate_offset(element_id)
        layup_info.get_analysis_plies(element_id)

    timer.add("loop")

    timer.summary()


def test_performance_local_field(dpf_server):
    """
    Document performance behaviour of local vs non-local fields
    """
    timer = Timer()

    files = get_data_files()
    setup_result = setup_operators(dpf_server, files)
    timer.add("Load data")

    data_non_local = setup_result.field.data
    timer.add("get data non-local")
    # Loop over .data property of non-local field is very slow
    for value in data_non_local:
        pass

    timer.add("loop non local")

    data_non_local = np.array(data_non_local)
    timer.add("to numpy array")
    # Loop over .data property of non-local field converted to numpy array is very fast
    for value in data_non_local:
        pass

    timer.add("loop non local numpy array")

    with setup_result.field.as_local_field() as f:
        data_local = f.data
        timer.add("get data local")
        # Loop over .data property of local field is very fast
        for value in data_local:
            pass

        timer.add("loop local")

    timer.summary()


def test_performance_property_dict(dpf_server):
    """
    Document performance behaviour of local vs non-local fields
    """
    timer = Timer()

    files = get_data_files()

    files = upload_continuous_fiber_composite_files_to_server(data_files=files, server=dpf_server)

    data_sources = get_composites_data_sources(files)
    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.data_sources(data_sources.rst)
    mesh = mesh_provider.outputs.mesh()
    timer.add("mesh")

    timer.add("Load data")

    material_operators = get_material_operators(
        rst_data_source=data_sources.rst, engineering_data_source=data_sources.engineering_data
    )
    layup_operators = add_layup_info_to_mesh(
        data_sources=data_sources, mesh=mesh, material_operators=material_operators
    )
    timer.add("After enrich mesh")

    property_dict = get_constant_property_dict(
        material_properties=[MaterialProperty.strain_limits_ext],
        materials_provider=material_operators.material_provider,
        data_source_or_streams_provider=data_sources.rst,
        mesh=mesh,
    )

    timer.add("After property dict")
    timer.summary()


def test_performance_flat(dpf_server):
    """
    This test shows how composite data can be stored
    in a numpy array. The numpy array can be used to
    efficiently implement additional postprocessing in python
    """
    timer = Timer()

    files = get_data_files()
    setup_result = setup_operators(dpf_server, files)
    timer.add("read data")

    layup_info = get_element_info_provider(
        setup_result.mesh,
        stream_provider_or_data_source=setup_result.streams_provider,
        no_bounds_checks=False,
    )
    timer.add("layup info")
    scope = setup_result.field.scoping.ids
    timer.add("scope")

    # number of rows = number of integration points
    # number of columns=12 (number of output properties)
    all_data = np.full((setup_result.field.elementary_data_count, 11), -1.0)
    start_index = 0

    indexer_data = _FieldIndexerWithDataPointer(setup_result.field)
    timer.add("indexer")

    with setup_result.mesh.elements.connectivities_field.as_local_field() as local_connectivity:

        timer.add("local connectivity")

        for element_id in scope:
            element_info = layup_info.get_element_info(element_id)
            if not element_info.is_layered:
                continue
            flat_indices = np.arange(
                0,
                (
                    element_info.n_spots
                    * element_info.number_of_nodes_per_spot_plane
                    * element_info.n_layers
                ),
            )

            unraveled_indices = np.unravel_index(
                flat_indices,
                (
                    element_info.n_layers,
                    element_info.n_spots,
                    element_info.number_of_nodes_per_spot_plane,
                ),
            )

            # Flat indices arrays (on value per data points)
            # Example for flat_node_indices with 4 nodes: [0,1,2,3,0,1,2,3,....]
            flat_layer_indices = unraveled_indices[0]
            flat_spot_indices = unraveled_indices[1]
            flat_node_indices = unraveled_indices[2]
            element_data = indexer_data.by_id(element_id)

            nodes = np.array(local_connectivity.get_entity_data_by_id(element_id))
            num_elementary_data = (
                element_info.n_spots
                * element_info.number_of_nodes_per_spot_plane
                * element_info.n_layers
            )
            end_index = start_index + num_elementary_data

            # Indices
            all_data[start_index:end_index, 0] = flat_layer_indices
            all_data[start_index:end_index, 1] = flat_spot_indices
            all_data[start_index:end_index, 2] = nodes[flat_node_indices]

            # Element data
            all_data[start_index:end_index, 3:9] = element_data
            all_data[start_index:end_index, 9] = element_info.element_type

            # dpf_material_ids
            all_data[start_index:end_index, 10] = element_info.dpf_material_ids[flat_layer_indices]
            start_index = start_index + num_elementary_data

        timer.add("loop")

    n_values_per_layers = 12

    # Test some layer indices
    assert all_data[:n_values_per_layers, 0] == pytest.approx(0)
    assert all_data[n_values_per_layers : 2 * n_values_per_layers, 0] == pytest.approx(1)

    # Test some spot indices
    layer_node_indices = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]
    assert all_data[:n_values_per_layers, 1] == pytest.approx(layer_node_indices)
    assert all_data[n_values_per_layers : 2 * n_values_per_layers, 1] == pytest.approx(
        layer_node_indices
    )

    # Test some node indices
    node_labels_first_element = (
        setup_result.mesh.elements.connectivities_field.get_entity_data_by_id(1)
    )
    layer_node_indices = np.tile(node_labels_first_element, 3)
    assert all_data[:n_values_per_layers, 2] == pytest.approx(layer_node_indices)
    assert all_data[n_values_per_layers : 2 * n_values_per_layers, 2] == pytest.approx(
        layer_node_indices
    )

    # Make sure strain data is available
    assert np.all(np.abs(all_data[:, 3:7]) > 1e-9)
    assert np.all(np.abs(all_data[:, 7:9]) < 1e-12)

    # Element type
    assert np.all(np.abs(all_data[:, 9]) == pytest.approx(181))

    # dpf_material_ids
    assert np.all(np.abs(all_data[:n_values_per_layers, 10]) == pytest.approx(3))
    assert np.all(
        np.abs(all_data[n_values_per_layers : 2 * n_values_per_layers, 10]) == pytest.approx(2)
    )

    timer.add("after local field")

    timer.summary()
