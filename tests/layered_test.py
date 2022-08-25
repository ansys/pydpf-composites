from contextlib import contextmanager
from dataclasses import dataclass
import os
import pathlib
import time

import ansys.dpf.core as dpf
import numpy as np
import pytest


@dataclass
class ElementInfo:
    n_layers: int
    n_corner_nodes: int
    n_spots: int
    is_layered: bool
    element_type: int


def get_selected_indices(element_info, layers=None, corner_nodes=None, spots=None):
    if layers is None:
        layer_indices = range(element_info.n_layers)
    else:
        layer_indices = layers

    if corner_nodes is None:
        corner_node_indices = range(element_info.n_corner_nodes)
    else:
        corner_node_indices = corner_nodes
    if spots is None:
        spot_indices = range(element_info.n_spots)
    else:
        spot_indices = spots

    # User cartesian after tests are in place
    all_indices = np.zeros(
        len(spot_indices) * len(corner_node_indices) * len(layer_indices), dtype=int
    )
    current_index = 0
    for layer_index in layer_indices:
        layer_start_index = layer_index * element_info.n_corner_nodes * element_info.n_spots
        for spot_index in spot_indices:
            spot_start_index = layer_start_index + spot_index * element_info.n_corner_nodes
            for corner_index in corner_node_indices:
                all_indices[current_index] = spot_start_index + corner_index
                current_index = current_index + 1

    return all_indices


class LayupInfo:
    def _get_corner_nodes(self, apdl_element_type):
        if apdl_element_type == 181:
            return 4
        raise Exception(f"Unsupported element type")

    def __init__(self, mesh, layer_indices, element_types_mapdl, element_types_dpf, n_spots=3):
        self.layer_indices = layer_indices

        self.layer_materials = mesh.property_field("element_layer_material_ids")
        self.apdl_element_type = element_types_mapdl
        self.dpf_element_type = element_types_dpf
        self.n_spots = n_spots
        self.mesh = mesh
        # selection_manager_provider= dpf.operators.metadata.mesh_selection_manager_provider()
        # selection_manager_provider.inputs.data_sources(rst_data_source)

    def get_element_info(self, element_id, field_data):
        n_values = field_data.shape[0]
        apdl_element_type = self.apdl_element_type.get_entity_data_by_id(element_id)
        is_layered = False
        n_layers = 1
        try:
            layer_data = self.layer_indices.get_entity_data_by_id(element_id)
            assert layer_data[0] + 1 == len(layer_data)
            n_layers = layer_data[0]
            is_layered = True
        except KeyError:
            pass
        assert int(n_values) % (int(n_layers) * int(self.n_spots)) == 0
        n_corner_nodes_computed = int(n_values / n_layers / self.n_spots)
        element_type = self.dpf_element_type.get_entity_data_by_id(element_id)
        n_corner_nodes_dpf = dpf.element_types.descriptor(element_type[0]).n_corner_nodes

        assert n_corner_nodes_dpf == n_corner_nodes_computed

        return ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=n_corner_nodes_dpf,
            n_spots=self.n_spots,
            is_layered=is_layered,
            element_type=apdl_element_type,
        )


@contextmanager
def get_layup_info(mesh):
    with mesh.property_field("element_layer_indices").as_local_field() as layer_indices:
        with mesh.property_field("apdl_element_type").as_local_field() as element_types_apdl:
            with mesh.elements.element_types_field.as_local_field() as element_types_dpf:
                yield LayupInfo(mesh, layer_indices, element_types_apdl, element_types_dpf)


class Timer:
    def __init__(self):
        self.timings = [("start", time.time())]

    def add(self, label):
        self.timings.append((label, time.time()))

    def summary(self):
        diffs = []
        for idx, timing in enumerate(self.timings):
            if idx > 0:
                diffs.append((timing[0], timing[1] - self.timings[idx - 1][1]))
        return diffs


def setup_operators(server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    if True:
        rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
        h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
        material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    if False:
        ger_path = (
            pathlib.Path("D:\\")
            / "ANSYSDev"
            / "additional_model_data_git"
            / "additional_model_data"
            / "ger89"
            / "ger89_files"
            / "dp0"
        )
        rst_path = ger_path / "SYS-1" / "MECH" / "file.rst"
        h5_path = ger_path / "ACP-Pre" / "ACP" / "ACPCompositeDefinitions.h5"
        material_path = ger_path / "SYS-1" / "MECH" / "MatML.xml"

    rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=server)

    h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=server)
    material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=server)

    rst_path = rst_server_path
    eng_data_path = material_server_path

    eng_data_source = dpf.DataSources()
    eng_data_source.add_file_path(eng_data_path, "EngineeringData")

    composite_definitions_source = dpf.DataSources()
    composite_definitions_source.add_file_path(h5_server_path, "CompositeDefinitions")

    rst_data_source = dpf.DataSources(rst_path)

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.data_sources(rst_data_source)
    mesh = mesh_provider.outputs.mesh()

    material_support_provider = dpf.Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.data_sources(rst_data_source)

    result_info_provider = dpf.Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = eng_data_source
    material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(eng_data_source)
    layup_provider = dpf.Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh_provider.outputs.mesh)
    layup_provider.inputs.data_sources(composite_definitions_source)
    layup_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    layup_provider.run()

    strain_operator = dpf.Operator("EPEL")
    strain_operator.inputs.data_sources(rst_data_source)
    strain_operator.inputs.bool_rotate_to_global(False)

    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)

    return (
        fields_container[0],
        mesh,
    )


def test_basic_workflow(dpf_server):
    field, mesh = setup_operators(dpf_server)

    component = 0

    def get_filtered_field(layers=None, corner_nodes=None, spots=None, scope=None):
        result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

        with result_field.as_local_field() as local_out_field:
            with field.as_local_field() as local_in_field, get_layup_info(mesh) as layup_info:
                if scope is None:
                    scope = local_in_field.scoping.ids
                for element_id in scope:
                    strain_data = local_in_field.get_entity_data_by_id(element_id)
                    element_info = layup_info.get_element_info(element_id, strain_data)
                    if element_info.is_layered:
                        selected_indices = get_selected_indices(
                            element_info, layers=layers, corner_nodes=corner_nodes, spots=spots
                        )
                        max_top_layer_xx_strain = strain_data[selected_indices][:, component]

                        local_out_field.append(max_top_layer_xx_strain, element_id)
                    else:
                        selected_indices = get_selected_indices(
                            element_info, layers=[0], corner_nodes=[2], spots=[2]
                        )
                        local_out_field.append(strain_data[selected_indices, component], element_id)
        return result_field

    result_field = get_filtered_field(layers=[5], corner_nodes=[3], spots=[2], scope=[1])
    assert result_field.get_entity_data_by_id(1) == pytest.approx(3.05458950e-03)

    result_field = get_filtered_field(layers=[0], spots=[2], scope=[1])
    assert result_field.get_entity_data_by_id(1) == pytest.approx(
        field.get_entity_data_by_id(1)[8:12, 0]
    )


def test_layered_properties(dpf_server):

    timer = Timer()
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    ger_path = (
        pathlib.Path("D:\\")
        / "ANSYSDev"
        / "additional_model_data_git"
        / "additional_model_data"
        / "ger89"
        / "ger89_files"
        / "dp0"
    )

    if False:
        rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
        h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
        material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    if True:
        rst_path = ger_path / "SYS-1" / "MECH" / "file.rst"
        h5_path = ger_path / "ACP-Pre" / "ACP" / "ACPCompositeDefinitions.h5"
        material_path = ger_path / "SYS-1" / "MECH" / "MatML.xml"

    rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=dpf_server)

    h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=dpf_server)
    material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=dpf_server)

    rst_path = rst_server_path
    eng_data_path = material_server_path

    eng_data_source = dpf.DataSources()
    eng_data_source.add_file_path(eng_data_path, "EngineeringData")

    composite_definitions_source = dpf.DataSources()
    composite_definitions_source.add_file_path(h5_server_path, "CompositeDefinitions")

    rst_data_source = dpf.DataSources(rst_path)

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.data_sources(rst_data_source)
    mesh = mesh_provider.outputs.mesh()

    material_support_provider = dpf.Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.data_sources(rst_data_source)

    result_info_provider = dpf.Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = eng_data_source
    material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(eng_data_source)
    layup_provider = dpf.Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh_provider.outputs.mesh)
    layup_provider.inputs.data_sources(composite_definitions_source)
    layup_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    layup_provider.run()

    timer.add("layup_provider")
    strain_operator = dpf.Operator("EPEL")
    strain_operator.inputs.data_sources(rst_data_source)
    strain_operator.inputs.bool_rotate_to_global(False)

    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)
    field = fields_container[0]

    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
    component = 0

    #    keyopt_8_provider = dpf.Operator("property_field_provider_by_name")
    #    keyopt_8_provider.inputs.data_sources(rst_data_source)

    timer.add("read_field")

    with result_field.as_local_field() as local_out_field:
        with field.as_local_field() as local_in_field, get_layup_info(mesh) as layup_info:
            timer.add("as local fields")

            for element_id in local_in_field.scoping.ids:
                try:
                    strain_data = local_in_field.get_entity_data_by_id(element_id)
                    element_info = layup_info.get_element_info(element_id, strain_data)
                    if element_info.is_layered:
                        selected_indices = get_selected_indices(
                            element_info, layers=[element_info.n_layers - 1], corner_nodes=[2]
                        )
                        #   selected_indices = get_selected_indices(element_info)
                        max_top_layer_xx_strain = np.max(
                            strain_data[selected_indices][:, component]
                        )

                        local_out_field.append([max_top_layer_xx_strain], element_id)
                    else:
                        pass
                        selected_indices = get_selected_indices(
                            element_info, layers=[0], corner_nodes=[2], spots=[2]
                        )
                        local_out_field.append(strain_data[selected_indices, component], element_id)

                except Exception as e:
                    #            print(element_info)
                    raise

    timer.add("loop")
    print("")
    print("====================")
    print(timer.summary())
    print("====================")


# mesh.plot(result_field)
