"""LayupInfo Provider."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Collection, Dict, List, Optional, Union, cast

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, MeshedRegion, Operator, PropertyField
import numpy as np
from numpy.typing import NDArray

from ansys.dpf.composites.indexer import (
    _FieldIndexerNoDataPointer,
    _FieldIndexerWithDataPointer,
    _PropertyFieldIndexerArrayValue,
    _PropertyFieldIndexerNoDataPointer,
    _PropertyFieldIndexerNoDataPointerNoBoundsCheck,
    _PropertyFieldIndexerSingleValue,
    _PropertyFieldIndexerWithDataPointer,
    _PropertyFieldIndexerWithDataPointerNoBoundsCheck,
)

_ANALYSIS_PLY_PREFIX = "AnalysisPly:"


def get_all_analysis_ply_names(mesh: MeshedRegion) -> Collection[str]:
    """Get all available analysis plies names."""
    return [
        property_field_name[len(_ANALYSIS_PLY_PREFIX) :]
        for property_field_name in mesh.available_property_fields
        if property_field_name.startswith(_ANALYSIS_PLY_PREFIX)
    ]


def _get_analysis_ply(mesh: MeshedRegion, name: str) -> PropertyField:
    ANALYSIS_PLY_PREFIX = "AnalysisPly:"
    property_field_name = ANALYSIS_PLY_PREFIX + name
    if property_field_name not in mesh.available_property_fields:
        available_analysis_plies = get_all_analysis_ply_names(mesh)
        raise RuntimeError(
            f"Analysis Ply not available: {name}. "
            f"Available analysis plies: {available_analysis_plies}"
        )
    return mesh.property_field(property_field_name)


@dataclass(frozen=True)
class ElementInfo:
    """Layup information for a given element.

    Use :class:`~ElementInfoProvider` to obtain a :class:`~ElementInfo` for a given element.

    Parameters
    ----------
    id
        Element id / Element Label
    n_layers
        number of layers. Equal to 1 for non-layered elements
    n_corner_nodes
        Number of corner nodes (without midside nodes).
    n_spots
        number of spots (through-the-thickness integration points) per layer
    element_type
        Apdl element type (e.g. 181 for layered shells)
    material_ids
        List of Dpf Material Ids for all layers
    is_shell
        True if the element is a shell element
    number_of_nodes_per_spot_plane
        Number of nodes per output plane.
        Equal to n_corner_nodes for shell elements and n_corner_nodes / 2
        for solid elements. Equal to -1 for non-layered elements.
    """

    id: int
    n_layers: int
    n_corner_nodes: int
    n_spots: int
    is_layered: bool
    element_type: int
    material_ids: List[int]
    is_shell: bool
    number_of_nodes_per_spot_plane: int


_supported_element_types = [181, 281, 185, 186, 187, 190]

"""
Map of keyopt_8 to number of spots.
Example: Element 181 with keyopt8==1 has two spots
"""
n_spots_by_element_type_and_keyopt_dict: Dict[int, Dict[int, int]] = {
    181: {0: 0, 1: 2, 2: 3},
    281: {0: 0, 1: 2, 2: 3},
    185: {0: 0, 1: 2},
    186: {0: 0, 1: 2},
    187: {0: 0},
    190: {0: 0, 1: 2},
}


def _is_shell(apdl_element_type: np.int64) -> bool:
    return {181: True, 281: True, 185: False, 186: False, 190: False, 187: False}[
        int(apdl_element_type)
    ]


def _get_n_spots(apdl_element_type: np.int64, keyopt_8: np.int64, keyopt_3: np.int64) -> int:

    if keyopt_3 == 0:
        if apdl_element_type == 185 or apdl_element_type == 186:
            return 0

    try:
        return n_spots_by_element_type_and_keyopt_dict[int(apdl_element_type)][int(keyopt_8)]
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
    corner_nodes_by_element_type: NDArray[np.int64] = np.full(
        np.amax(all_element_types) + 1, -1, dtype=np.int64
    )

    corner_nodes_by_element_type[all_element_types] = [
        dpf.element_types.descriptor(element_type).n_corner_nodes
        if dpf.element_types.descriptor(element_type).n_corner_nodes is not None
        else -1
        for element_type in all_element_types
    ]
    return corner_nodes_by_element_type


class AnalysisPlyInfoProvider:
    """AnalysisPlyInfoProvider. Can be used to compute the layer indices of a given analysis ply.

    Parameters
    ----------
    mesh
        Dpf MeshedRegion with layup information.
    name
        Analysis Ply Name
    """

    def __init__(self, mesh: MeshedRegion, name: str):
        """Initialize AnalysisPlyProvider."""
        self.name = name
        self.property_field = _get_analysis_ply(mesh, name)
        self._layer_indices = _PropertyFieldIndexerNoDataPointer(self.property_field)

    def get_layer_index_by_element_id(self, element_id: int) -> Optional[np.int64]:
        """Get the layer index for the analysis ply in a given element.

        Parameters
        ----------
        element_id: int
            Element id, Element label

        """
        return self._layer_indices.by_id(element_id)


def get_dpf_material_id_by_analyis_ply_map(
    mesh: MeshedRegion,
    data_source_or_streams_provider: Union[DataSources, Operator],
) -> Dict[str, int]:
    """Get Dict that maps analysis ply names to dpf_material_ids.

    Parameters
    ----------
    mesh
        Dpf Meshed region enriched with layup information
    data_source_or_streams_provider
    """
    analysis_ply_to_material_map = {}
    element_info_provider = get_element_info_provider(
        mesh=mesh, stream_provider_or_data_source=data_source_or_streams_provider
    )

    for analysis_ply_name in get_all_analysis_ply_names(mesh):
        analysis_ply_info_provider = AnalysisPlyInfoProvider(mesh, analysis_ply_name)
        first_element_id = analysis_ply_info_provider.property_field.scoping.ids[0]
        element_info = element_info_provider.get_element_info(first_element_id)
        assert element_info is not None
        layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(first_element_id)
        analysis_ply_to_material_map[analysis_ply_name] = element_info.material_ids[
            cast(int, layer_index)
        ]

    return analysis_ply_to_material_map


class ElementInfoProvider:
    """Provider for :class:`~ElementInfo`.

    Use :func:`~get_element_info_provider` to create :class:`~ElementInfoProvider`
    objects.

    Initialize the class before a loop and
    call :func:`~get_element_info` for each element.


    Parameters
    ----------
    mesh
    layer_indices
    element_types_apdl
    element_types_dpf
    keyopt_8_values
    keyopt_3_values
    material_ids
    no_bounds_checks
        Disable bounds checks.
        Results in better performance but potentially cryptic
        error messages
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
        """Initialize ElementInfoProvider."""
        # Note: Every property we add to element info adds some performance
        # overhead for all the calls to get_element info. We should keep it
        # focused on the most important properties. We can add different providers
        # for other properties (such as thickness and angles)

        def get_indexer_with_data_pointer(field: PropertyField) -> _PropertyFieldIndexerArrayValue:
            if no_bounds_checks:
                return _PropertyFieldIndexerWithDataPointerNoBoundsCheck(field)
            else:
                return _PropertyFieldIndexerWithDataPointer(field)

        def get_indexer_no_data_pointer(field: PropertyField) -> _PropertyFieldIndexerSingleValue:
            if no_bounds_checks:
                return _PropertyFieldIndexerNoDataPointerNoBoundsCheck(field)
            else:
                return _PropertyFieldIndexerNoDataPointer(field)

        # Has to be always with bounds checks because it does not contain
        # data for all the elements
        self.layer_indices = _PropertyFieldIndexerWithDataPointer(layer_indices)
        self.layer_materials = get_indexer_with_data_pointer(material_ids)

        self.apdl_element_types = get_indexer_no_data_pointer(element_types_apdl)
        self.dpf_element_types = get_indexer_no_data_pointer(element_types_dpf)
        self.keyopt_8_values = get_indexer_no_data_pointer(keyopt_8_values)
        self.keyopt_3_values = get_indexer_no_data_pointer(keyopt_3_values)

        self.mesh = mesh
        self.corner_nodes_by_element_type = _get_corner_nodes_by_element_type_array()

    def get_element_info(self, element_id: int) -> Optional[ElementInfo]:
        """Get :class:`~ElementInfo` for a given element id.

        Parameters
        ----------
        element_id: Element Id/Label

        Returns
        -------
        Optional[ElementInfo]
            Returns None if element type is not supported
        """
        is_layered = False
        n_layers = 1

        keyopt_8 = self.keyopt_8_values.by_id(element_id)
        keyopt_3 = self.keyopt_3_values.by_id(element_id)
        apdl_element_type = self.apdl_element_types.by_id(element_id)

        if keyopt_3 is None or keyopt_8 is None or apdl_element_type is None:
            raise RuntimeError(
                "Could not determine element properties. Probably they were requested for an"
                f" invalid element id. Element id: {element_id}"
            )

        if int(apdl_element_type) not in _supported_element_types:
            return None

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
        number_of_nodes_per_spot_plane = -1
        if is_layered:
            number_of_nodes_per_spot_plane = corner_nodes_dpf if is_shell else corner_nodes_dpf // 2
        return ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=int(apdl_element_type),
            material_ids=material_ids,
            id=element_id,
            is_shell=is_shell,
            number_of_nodes_per_spot_plane=number_of_nodes_per_spot_plane,
        )


def get_element_info_provider(
    mesh: MeshedRegion,
    stream_provider_or_data_source: Union[Operator, DataSources],
    no_bounds_checks: bool = False,
) -> ElementInfoProvider:
    """Get :class:`~ElementInfoProvider` Object.

    Parameters
    ----------
    mesh
    stream_provider_or_data_source
        dpf stream provider or dpf data source
    no_bounds_checks
        Disable bounds checks. Improves
        performance but can result in cryptic error messages

    Returns
    -------
    ElementInfoProvider

    Notes
    -----
        Either a data_source or a stream_provider is required
    """

    def get_keyopt_property_field(keyopt: int) -> PropertyField:
        keyopt_provider = dpf.Operator("property_field_provider_by_name")
        if isinstance(stream_provider_or_data_source, Operator):
            keyopt_provider.inputs.streams_container(stream_provider_or_data_source)
        else:
            keyopt_provider.inputs.data_sources(stream_provider_or_data_source)

        keyopt_provider.inputs.property_name(f"keyopt_{keyopt}")
        return keyopt_provider.outputs.property_field()

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

    return ElementInfoProvider(mesh, **fields, no_bounds_checks=no_bounds_checks)


class LayupProperty(Enum):
    """Enum for Layup Properties.

    Values correspond to labels in output container of layup provider.
    """

    Angle = 0
    ShearAngle = 1
    Thickness = 2
    LaminateOffset = 3


class LayupPropertiesProvider:
    """Provider for layup properties.

    Parameters
    ----------
    layup_provider
    """

    def __init__(self, layup_provider: Operator):
        """Initialize LayupProperties provider."""
        layup_outputs_container = layup_provider.outputs.fields_container()
        composite_label = layup_outputs_container.labels[0]
        angle_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.Angle.value}
        )
        self._angle_indexer = _FieldIndexerWithDataPointer(angle_field)
        thickness_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.Thickness.value}
        )
        self._thickness_indexer = _FieldIndexerWithDataPointer(thickness_field)
        shear_angle_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.ShearAngle.value}
        )
        self._shear_angle_indexer = _FieldIndexerWithDataPointer(shear_angle_field)
        offset_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.LaminateOffset.value}
        )
        self._offset_indexer = _FieldIndexerNoDataPointer(offset_field)

    def get_element_angles(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get angles for all layers. Returns None if element is not layered todo: test."""
        return self._angle_indexer.by_id(element_id)

    def get_element_thicknesses(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get thicknesses for all layers. Returns None if element is not layered."""
        return self._thickness_indexer.by_id(element_id)

    def get_element_shear_angles(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get shear angle for all layers. Returns None if element is not layered."""
        return self._shear_angle_indexer.by_id(element_id)

    def get_element_laminate_offset(self, element_id: int) -> Optional[np.double]:
        """Get laminate offset of element. Returns None if element is not layered."""
        return self._offset_indexer.by_id(element_id)
