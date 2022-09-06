import contextlib
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, List

import ansys.dpf.core as dpf
import numpy as np
from numpy.typing import NDArray


@contextmanager
def get_analysis_ply(mesh: Any, name: str) -> Any:
    ANALYSIS_PLY_PREFIX = "AnalysisPly:"

    with mesh.property_field(
        ANALYSIS_PLY_PREFIX + name
    ).as_local_field() as analysis_ply_property_field:
        yield analysis_ply_property_field


@dataclass
class ElementInfo:
    n_layers: int
    n_corner_nodes: int
    n_spots: int
    is_layered: bool
    element_type: int
    material_ids: List[int]


def setup_index_by_id(scoping: Any) -> Any:
    # Setup array that can be indexed by id to get the index.
    # For ids which are not present in the scoping the array has a value of -1
    indices: Any = np.ones(max(scoping.ids) + 1, dtype=int) * -1
    indices[scoping.ids] = np.arange(len(scoping.ids))
    return indices


class _IndexerNoDataPointer:
    def __init__(self, array: Any):
        self.indices = setup_index_by_id(array.scoping)
        self.data = array.data

    def by_id(self, entity_id: int) -> Any:
        return self.data[self.indices[entity_id]]


class _IndexerWithDataPointer:
    def __init__(self, array: Any):
        self.indices = setup_index_by_id(array.scoping)
        self.data = array.data
        self._data_pointer = np.append(array._data_pointer, len(self.data))  # type: ignore

    def by_id(self, entity_id: int) -> Any:
        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return self.data[self._data_pointer[idx] : self._data_pointer[idx + 1]]


# Todo: Extend for more element types
def _get_n_spots(apdl_element_type: int, keyopt_8: int) -> int:
    if apdl_element_type == 181:
        if keyopt_8 == 2:
            return 3
    raise Exception(f"Unsupported element type")


def _get_corner_nodes_by_element_type_array() -> NDArray[Any]:
    # Precompute n_corner_nodes for all element types
    # self.corner_nodes_by_element_type by can be indexed by element type to get the number of
    # corner nodes
    all_element_types = [int(e.value) for e in dpf.element_types if e.value >= 0]
    corner_nodes_by_element_type: NDArray[Any] = (
        np.ones(np.amax(all_element_types) + 1, dtype=int) * -1
    )
    corner_nodes_by_element_type[all_element_types] = [
        dpf.element_types.descriptor(element_type).n_corner_nodes
        if dpf.element_types.descriptor(element_type).n_corner_nodes is not None
        else -1
        for element_type in all_element_types
    ]
    return corner_nodes_by_element_type


class LayupInfo:
    """
    Provider for ElementInfo. Precomputes id to index maps for all
    property fields to improve performance
    """

    def __init__(
        self,
        mesh: Any,
        layer_indices: Any,
        element_types_apdl: Any,
        element_types_dpf: Any,
        keyopt_8: Any,
        material_ids: Any,
    ):
        self.layer_indices = _IndexerWithDataPointer(layer_indices)
        self.layer_materials = _IndexerWithDataPointer(material_ids)

        self.apdl_element_type = _IndexerNoDataPointer(element_types_apdl)
        self.dpf_element_type = _IndexerNoDataPointer(element_types_dpf)
        self.keyopt_8 = _IndexerNoDataPointer(keyopt_8)

        self.mesh = mesh
        self.corner_nodes_by_element_type = _get_corner_nodes_by_element_type_array()

    def get_element_info(self, element_id: int) -> ElementInfo:
        apdl_element_type = self.apdl_element_type.by_id(element_id)
        is_layered = False
        n_layers = 1
        keyopt_8 = self.keyopt_8.by_id(element_id)
        n_spots = _get_n_spots(apdl_element_type, keyopt_8)
        material_ids: Any = []

        layer_data = self.layer_indices.by_id(element_id)
        if layer_data is not None:
            material_ids = self.layer_materials.by_id(element_id)
            assert material_ids is not None
            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True

        element_type = self.dpf_element_type.by_id(element_id)

        corner_nodes_dpf = self.corner_nodes_by_element_type[element_type]
        if corner_nodes_dpf < 0:
            raise Exception(f"Invalid number of corner nodes for element with type {element_type}")

        return ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=apdl_element_type,
            material_ids=material_ids,
        )


@contextmanager
def get_layup_info(mesh: Any, rst_data_source: Any) -> Any:
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
