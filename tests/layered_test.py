import contextlib
from contextlib import contextmanager
from dataclasses import dataclass
import os
import pathlib
import time
from typing import Any, List

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
    material_ids: List[int]


def get_selected_indices(element_info: ElementInfo, layers=None, corner_nodes=None, spots=None):
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


def get_selected_indices_by_material_id(element_info: ElementInfo, material_id: int):
    layer_indices = [
        index for index, mat_id in enumerate(element_info.material_ids) if mat_id == material_id
    ]
    return get_selected_indices(element_info, layers=layer_indices)


class LayupInfo:
    def _get_n_spots(self, apdl_element_type, keyopt_8):
        if apdl_element_type == 181:
            if keyopt_8 == 2:
                return 3
        raise Exception(f"Unsupported element type")

    def __init__(
        self, mesh, layer_indices, element_types_apdl, element_types_dpf, keyopt_8, material_ids
    ):
        self.layer_indices = layer_indices

        self.layer_materials = material_ids
        self.apdl_element_type = element_types_apdl
        self.dpf_element_type = element_types_dpf
        self.mesh = mesh
        self.keyopt_8 = keyopt_8

    def get_element_info(self, element_id, field_data):
        n_values = field_data.shape[0]
        apdl_element_type = self.apdl_element_type.get_entity_data_by_id(element_id)
        is_layered = False
        n_layers = 1
        keyopt_8 = self.keyopt_8.get_entity_data_by_id(element_id)
        n_spots = self._get_n_spots(apdl_element_type, keyopt_8)
        material_ids = []

        try:
            layer_data = self.layer_indices.get_entity_data_by_id(element_id)
            material_ids = self.layer_materials.get_entity_data_by_id(element_id)

            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True
        except KeyError:
            pass
        assert int(n_values) % (int(n_layers) * int(n_spots)) == 0, "Inconsistent number of data"

        n_corner_nodes_computed = int(n_values / n_layers / n_spots)
        element_type = self.dpf_element_type.get_entity_data_by_id(element_id)
        n_corner_nodes_dpf = dpf.element_types.descriptor(element_type[0]).n_corner_nodes

        assert (
            n_corner_nodes_dpf == n_corner_nodes_computed
        ), "Computed nodes not equal corner nodes"

        return ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=n_corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=apdl_element_type,
            material_ids=material_ids,
        )


@contextmanager
def get_layup_info(mesh, rst_data_source):
    keyopt_8_provider = dpf.Operator("property_field_provider_by_name")
    keyopt_8_provider.inputs.data_sources(rst_data_source)
    keyopt_8_provider.inputs.property_name("keyopt_8")
    key_opt_8_field = keyopt_8_provider.outputs.property_field()

    fields = {
        "layer_indices": mesh.property_field("element_layer_indices"),
        "element_types_apdl": mesh.property_field("apdl_element_type"),
        "element_types_dpf": mesh.elements.element_types_field.as_local_field(),
        "keyopt_8": key_opt_8_field,
        "material_ids": mesh.property_field("element_layered_material_ids"),
    }

    with contextlib.ExitStack() as stack:
        context_dict = {
            key: stack.enter_context(value.as_local_field()) for key, value in fields.items()
        }

        yield LayupInfo(mesh, **context_dict)


@dataclass
class FieldInfo:
    field: Any
    layup_info: LayupInfo


@contextmanager
def get_field_info(input_field, mesh, rst_data_source):
    with input_field.as_local_field() as local_input_field:
        with get_layup_info(mesh, rst_data_source=rst_data_source) as layup_info:
            yield FieldInfo(field=local_input_field, layup_info=layup_info)


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


def setup_operators(server, rst_path, h5_path, material_path):
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

    return (fields_container[0], mesh, rst_data_source)


def get_result_field(
    field_info, layers=None, corner_nodes=None, spots=None, scope=None, material_id=None
):
    component = 0
    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
    with result_field.as_local_field() as local_result_field:
        if scope is None:
            scope = field_info.field.scoping.ids
        for element_id in scope:
            strain_data = field_info.field.get_entity_data_by_id(element_id)
            element_info = field_info.layup_info.get_element_info(element_id, strain_data)
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
                selected_indices = get_selected_indices(
                    element_info, layers=[0], corner_nodes=[2], spots=[2]
                )
                local_result_field.append(strain_data[selected_indices, component], element_id)
    return result_field


def test_basic_workflow(dpf_server):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")

    input_field, mesh, rst_data_source = setup_operators(
        dpf_server, rst_path=rst_path, material_path=material_path, h5_path=h5_path
    )

    with get_field_info(
        input_field=input_field, mesh=mesh, rst_data_source=rst_data_source
    ) as field_info:
        result_field = get_result_field(
            field_info, layers=[5], corner_nodes=[3], spots=[2], scope=[1]
        )

        assert result_field.get_entity_data_by_id(1) == pytest.approx(3.05458950e-03)

        result_field = get_result_field(field_info, layers=[0], spots=[2], scope=[1])

        assert result_field.get_entity_data_by_id(1) == pytest.approx(
            input_field.get_entity_data_by_id(1)[8:12, 0]
        )

        # Material 2 is present in layer 1,2 and 4
        result_field_by_mat = get_result_field(field_info, material_id=2)
        result_field_layer = get_result_field(field_info, layers=[1, 2, 4])

        assert result_field_by_mat.get_entity_data_by_id(1) == pytest.approx(
            result_field_layer.get_entity_data_by_id(1)
        )


def test_basic_performance(dpf_server):
    timer = Timer()

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

    input_field, mesh, rst_data_source = setup_operators(
        dpf_server, rst_path=rst_path, material_path=material_path, h5_path=h5_path
    )

    with get_field_info(
        input_field=input_field, mesh=mesh, rst_data_source=rst_data_source
    ) as field_info:
        timer.add("start")

        result_field = get_result_field(field_info, layers=[5], corner_nodes=[3], spots=[2])

        timer.add("filter_single_value")
        result_field = get_result_field(field_info, layers=[0], spots=[2])

        timer.add("filter list of values")

        # Material 2 is present in layer 1,2 and 4
        result_field_by_mat = get_result_field(field_info, material_id=2)

        timer.add("filter by material")
        print(timer.summary())
