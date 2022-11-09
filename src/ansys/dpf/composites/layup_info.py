"""LayupInfo Provider."""

from dataclasses import dataclass
import sys
from typing import Any, Dict, List, Union, cast

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, Field, MeshedRegion, PropertyField, Scoping
import numpy as np
from numpy.typing import NDArray


def get_analysis_ply(mesh: MeshedRegion, name: str) -> PropertyField:
    """Return analysis ply property field.

    :param mesh: dpf meshed region
    :param name:
    :return: analysis_ply local property field contextmanager
    """
    ANALYSIS_PLY_PREFIX = "AnalysisPly:"
    property_field_name = ANALYSIS_PLY_PREFIX + name
    if property_field_name not in mesh.available_property_fields:
        available_analysis_plies = [
            property_field_name
            for property_field_name in mesh.available_property_fields
            if property_field_name.startswith(ANALYSIS_PLY_PREFIX)
        ]
        raise RuntimeError(
            f"Analysis Ply not available: {name}. "
            f"Available analysis plies: {available_analysis_plies}"
        )
    return mesh.property_field(property_field_name)


@dataclass
class ElementInfo:
    """Layup information for a given element."""

    id: int
    n_layers: int
    n_corner_nodes: int
    n_spots: int
    is_layered: bool
    element_type: int
    material_ids: List[int]
    is_shell: bool
    # -1 for non-layered elements
    nodes_per_layer: int


def _setup_index_by_id(scoping: Scoping) -> NDArray[np.int64]:
    # Setup array that can be indexed by id to get the index.
    # For ids which are not present in the scoping the array has a value of -1
    indices: NDArray[np.int64] = np.full(max(scoping.ids) + 1, -1, dtype=np.int64)
    indices[scoping.ids] = np.arange(len(scoping.ids))
    return indices


class _Indexer(Protocol):
    def by_id(self, entity_id: int) -> Any:
        pass


class _IndexerNoDataPointer:
    def __init__(self, field: Union[Field, PropertyField]):
        self.indices = _setup_index_by_id(field.scoping)
        # The next call accesses the numpy data. This sends the data over grpc which takes some time
        # Without converting this to a numpy array, performance during the lookup is about 50%.
        # It is not clear why. To be checked with dpf team. If this is a local field there is no
        # performance difference because the local field implementation already returns a numpy
        # array
        self.data: NDArray[Any] = np.array(field.data)
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Any:
        if entity_id > self.max_id:
            return None
        return self.data[self.indices[entity_id]]


class _IndexerNoDataPointerNoBoundsCheck:
    def __init__(self, field: Union[Field, PropertyField]):
        self.indices = _setup_index_by_id(field.scoping)
        # The next call accesses the numpy data. This sends the data over grpc which takes some time
        # Without converting this to a numpy array, performance during the lookup is about 50%.
        # It is not clear why. To be checked with dpf team. If this is a local field there is no
        # performance difference because the local field implementation already returns a numpy
        # array
        self.data: NDArray[Any] = np.array(field.data)

    def by_id(self, entity_id: int) -> Any:
        return self.data[self.indices[entity_id]]


class _IndexerWithDataPointer:
    def __init__(self, field: Union[Field, PropertyField]):
        self.indices = _setup_index_by_id(field.scoping)
        # The next call accesses the numpy data. This sends the data over grpc which takes some time
        # Without converting this to a numpy array, performance during the lookup is about 50%.
        # It is not clear why. To be checked with dpf team. If this is a local field there is no
        # performance difference because the local field implementation already returns a numpy
        # array
        self.data: NDArray[Any] = np.array(field.data)
        # The data pointer only contains the start index of each element. We add the end to make
        # it easier to use
        self._data_pointer: NDArray[np.int64] = np.append(  # type: ignore
            field._data_pointer, len(self.data)
        )
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Any:
        if entity_id > self.max_id:
            return None

        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return self.data[self._data_pointer[idx] : self._data_pointer[idx + 1]]


class _IndexerWithDataPointerNoBoundsCheck:
    def __init__(self, field: Union[Field, PropertyField]):
        self.indices = _setup_index_by_id(field.scoping)
        # The next call accesses the numpy data. This sends the data over grpc which takes some time
        # Without converting this to a numpy array, performance during the lookup is about 50%.
        # It is not clear why. To be checked with dpf team. If this is a local field there is no
        # performance difference because the local field implementation already returns a numpy
        # array
        self.data: NDArray[Any] = np.array(field.data)
        # The data pointer only contains the start index of each element. We add the end to make
        # it easier to use
        self._data_pointer: NDArray[np.int64] = np.append(  # type: ignore
            field._data_pointer, len(self.data)
        )
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Any:
        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return self.data[self._data_pointer[idx] : self._data_pointer[idx + 1]]


"""
Map of keyopt_8 to number of spots.
Example: Element 181 with keyopt8==1 has two spots
"""
n_spots_by_element_type_and_keyopt_dict: Dict[int, Dict[int, int]] = {
    181: {0: 0, 1: 2, 2: 3},
    281: {0: 0, 1: 2, 2: 3},
    185: {0: 0, 1: 2},
    186: {0: 0, 1: 2},
    190: {0: 0, 1: 2},
}


def _is_shell(apdl_element_type: int) -> bool:
    return {181: True, 281: True, 185: False, 186: False, 190: False}[apdl_element_type]


def _get_n_spots(apdl_element_type: int, keyopt_8: int, keyopt_3: int) -> int:

    if keyopt_3 == 0:
        if apdl_element_type == 185 or apdl_element_type == 186:
            return 0

    try:
        return n_spots_by_element_type_and_keyopt_dict[apdl_element_type][keyopt_8]
    except KeyError:
        raise RuntimeError(
            f"Unsupported element type keyopt8 combination "
            f"Apdl Element Type: {apdl_element_type} "
            f"keyopt8: {keyopt_8}."
        )


def _get_corner_nodes_by_element_type_array() -> NDArray[np.int64]:
    # Precompute n_corner_nodes for all element types
    # corner_nodes_by_element_type by can be indexed by element type to get the number of
    # corner nodes. If negative value is returned number of corner nodes is not available.
    all_element_types = [int(e.value) for e in dpf.element_types if e.value >= 0]
    corner_nodes_by_element_type: NDArray[np.int64] = (
        np.ones(np.amax(all_element_types) + 1, dtype=np.int64) * -1
    )

    corner_nodes_by_element_type[all_element_types] = [
        dpf.element_types.descriptor(element_type).n_corner_nodes
        if dpf.element_types.descriptor(element_type).n_corner_nodes is not None
        else -1
        for element_type in all_element_types
    ]
    return corner_nodes_by_element_type


class AnalysisPlyInfoProvider:
    """AnalysisPlyInfoProvider. Provides layer indices by element id."""

    def __init__(self, mesh: MeshedRegion, name: str):
        """Initialize AnalysisPlyInfoProvider object and precompute indices.

        :param analysis_ply_property_field: analysis ply property field

        """
        self.name = name
        self.property_field = get_analysis_ply(mesh, name)
        self._layer_indices = _IndexerNoDataPointer(self.property_field)

    def get_layer_index_by_element_id(self, element_id: int) -> int:
        """Get the layer index for the analysis ply in a given element."""
        try:
            return cast(int, self._layer_indices.by_id(element_id))
        except IndexError:
            return -1


class ElementInfoProvider:
    """Provider for ElementInfo.

    Precomputes id to index maps for all
    property fields to improve performance

    Note: Every property we add to element info adds some performance
    overhead for all the calls to get_element info. We should keep it
    focused on the most important properties. We can add different providers
    for other properties (such as thickness and angles)
    """

    def __init__(
        self,
        mesh: MeshedRegion,
        layer_indices: PropertyField,
        element_types_apdl: PropertyField,
        element_types_dpf: PropertyField,
        keyopt_8_values: PropertyField,
        keyopt_3_values: PropertyField,
        material_ids: PropertyField,
        no_bounds_checks: bool = False,
    ):
        """Initialize LayupInfo object and precompute indices.

        :param mesh: dpf meshed region
        :param layer_indices: layer_indices property field
        :param element_types_apdl: apdl_element_types property_field
        :param element_types_dpf: dpf_element_types property field
        :param keyopt_8_values: keyopt_8 property field
        :param material_ids: material_ids property field
        :param no_bounds_checks: Disable bounds checks.
                Results in better performance but potentially cryptic
                error messages
        """

        def get_indexer_with_data_pointer(field: Union[Field, PropertyField]) -> _Indexer:
            if no_bounds_checks:
                return _IndexerWithDataPointerNoBoundsCheck(field)
            else:
                return _IndexerWithDataPointer(field)

        def get_indexer_no_data_pointer(field: Union[Field, PropertyField]) -> _Indexer:
            if no_bounds_checks:
                return _IndexerNoDataPointerNoBoundsCheck(field)
            else:
                return _IndexerNoDataPointer(field)

        self.layer_indices = get_indexer_with_data_pointer(layer_indices)
        self.layer_materials = get_indexer_with_data_pointer(material_ids)

        self.apdl_element_types = get_indexer_no_data_pointer(element_types_apdl)
        self.dpf_element_types = get_indexer_no_data_pointer(element_types_dpf)
        self.keyopt_8_values = get_indexer_no_data_pointer(keyopt_8_values)
        self.keyopt_3_values = get_indexer_no_data_pointer(keyopt_3_values)

        self.mesh = mesh
        self.corner_nodes_by_element_type = _get_corner_nodes_by_element_type_array()

    def get_element_info(self, element_id: int) -> ElementInfo:
        """Get ElementInfo Object for a given element id."""
        apdl_element_type = self.apdl_element_types.by_id(element_id)
        is_layered = False
        n_layers = 1
        keyopt_8 = self.keyopt_8_values.by_id(element_id)
        keyopt_3 = self.keyopt_3_values.by_id(element_id)
        if keyopt_3 is None or keyopt_8 is None or apdl_element_type is None:
            raise RuntimeError(
                "Could not determine element properties. Probably they were requested for an"
                f" invalid element id. Element id: {element_id}"
            )
        n_spots = _get_n_spots(apdl_element_type, keyopt_8, keyopt_3)
        material_ids: Any = []
        element_type = self.dpf_element_types.by_id(element_id)

        layer_data = self.layer_indices.by_id(element_id)
        if layer_data is not None:
            material_ids = self.layer_materials.by_id(element_id)
            assert material_ids is not None
            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True

        corner_nodes_dpf = self.corner_nodes_by_element_type[element_type]
        if corner_nodes_dpf < 0:
            raise Exception(f"Invalid number of corner nodes for element with type {element_type}")
        is_shell = _is_shell(apdl_element_type)
        nodes_per_layer = -1
        if is_layered:
            nodes_per_layer = corner_nodes_dpf if is_shell else corner_nodes_dpf // 2
        return ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=apdl_element_type,
            material_ids=material_ids,
            id=element_id,
            is_shell=is_shell,
            nodes_per_layer=nodes_per_layer,
        )


def get_element_info_provider(
    mesh: MeshedRegion, rst_data_source: DataSources
) -> ElementInfoProvider:
    """Get LayupInfo Object.

    :param mesh: dpf meshed region
    :param rst_data_source: dpf datasource
    :return: LayupInfo
    """

    def get_keyopt_property_field(keyopt: int) -> PropertyField:
        keyopt_8_provider = dpf.Operator("property_field_provider_by_name")
        keyopt_8_provider.inputs.data_sources(rst_data_source)
        keyopt_8_provider.inputs.property_name(f"keyopt_{keyopt}")
        return keyopt_8_provider.outputs.property_field()

    requested_property_fields = [
        "apdl_element_type",
        "element_layer_indices",
        "element_layered_material_ids",
    ]

    for property_field_name in requested_property_fields:
        if property_field_name not in mesh.available_property_fields:
            message = f"Missing property field in mesh: '{property_field_name}'."
            if property_field_name in ["element_layer_indices", "element_layer_material_ids"]:
                message += " Maybe you have to run the layup provider operator first."
            raise RuntimeError(message)
    fields = {
        "layer_indices": mesh.property_field("element_layer_indices"),
        "element_types_apdl": mesh.property_field("apdl_element_type"),
        "element_types_dpf": mesh.elements.element_types_field,
        "keyopt_8_values": get_keyopt_property_field(8),
        "keyopt_3_values": get_keyopt_property_field(3),
        "material_ids": mesh.property_field("element_layered_material_ids"),
    }

    return ElementInfoProvider(mesh, **fields)
