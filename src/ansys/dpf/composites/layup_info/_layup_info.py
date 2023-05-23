"""Lay-up information provider."""

from dataclasses import dataclass
from typing import Any, Collection, Dict, List, Optional, Sequence, Union, cast

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, MeshedRegion, Operator, PropertyField
import numpy as np
from numpy.typing import NDArray

from .._indexer import (
    FieldIndexerNoDataPointer,
    FieldIndexerWithDataPointer,
    PropertyFieldIndexerArrayValue,
    PropertyFieldIndexerNoDataPointer,
    PropertyFieldIndexerNoDataPointerNoBoundsCheck,
    PropertyFieldIndexerSingleValue,
    PropertyFieldIndexerWithDataPointer,
    PropertyFieldIndexerWithDataPointerNoBoundsCheck,
)
from ._enums import LayupProperty

_ANALYSIS_PLY_PREFIX = "AnalysisPly:"


def get_all_analysis_ply_names(mesh: MeshedRegion) -> Collection[str]:
    """Get names of all available analysis plies."""
    return [
        property_field_name[len(_ANALYSIS_PLY_PREFIX) :]
        for property_field_name in mesh.available_property_fields
        if property_field_name.startswith(_ANALYSIS_PLY_PREFIX)
    ]


def _get_analysis_ply(mesh: MeshedRegion, name: str, skip_check: bool = False) -> PropertyField:
    ANALYSIS_PLY_PREFIX = "AnalysisPly:"
    property_field_name = ANALYSIS_PLY_PREFIX + name

    # Because this test can be slow, it can be skipped
    if not skip_check and property_field_name not in mesh.available_property_fields:
        available_analysis_plies = get_all_analysis_ply_names(mesh)
        raise RuntimeError(
            f"Analysis ply is not available: {name}. "
            f"Available analysis plies: {available_analysis_plies}"
        )
    return mesh.property_field(property_field_name)


@dataclass(frozen=True)
class ElementInfo:
    """Provides lay-up information for an element.

    Use the :class:`~ElementInfoProvider` class to obtain the
    :class:`~ElementInfo` class for an element.

    Parameters
    ----------
    id
        Element ID or label.
    n_layers
        Number of layers. For non-layered elements, the value is ``1``.
    n_corner_nodes
        Number of corner nodes (without midside nodes).
    n_spots
        Number of spots (through-the-thickness integration points) per layer.
    element_type
        APDL element type. For example, ``181`` for layered shells.
    dpf_material_ids
        List of DPF material IDs for all layers.
    is_shell
        Whether the element is a shell element.
    number_of_nodes_per_spot_plane
        Number of nodes per output plane. The value is equal
        to ``n_corner_nodes`` for shell elements and ``n_corner_nodes``
        divided by two for layered solid elements. The value is equal to ``-1``
        for non-layered elements.
    """

    id: int
    n_layers: int
    n_corner_nodes: int
    n_spots: int
    is_layered: bool
    element_type: int
    dpf_material_ids: NDArray[np.int64]
    is_shell: bool
    number_of_nodes_per_spot_plane: int


_supported_element_types = [181, 281, 185, 186, 187, 190]

"""
Map of keyopt_8 to number of spots.
Example: Element 181 with keyopt8==1 has two spots
"""
_n_spots_by_element_type_and_keyopt_dict: Dict[int, Dict[int, int]] = {
    181: {0: 0, 1: 2, 2: 3},
    281: {0: 0, 1: 2, 2: 3},
    185: {0: 0, 1: 2},
    186: {0: 0, 1: 2},
    187: {0: 0},
    190: {0: 0, 1: 2},
}


def _is_shell(apdl_element_type: np.int64) -> bool:
    return {181: True, 281: True, 185: False, 186: False, 187: False, 190: False}[
        int(apdl_element_type)
    ]


def _get_n_spots(apdl_element_type: np.int64, keyopt_8: np.int64, keyopt_3: np.int64) -> int:
    if keyopt_3 == 0:
        if apdl_element_type == 185 or apdl_element_type == 186:
            return 0

    try:
        return _n_spots_by_element_type_and_keyopt_dict[int(apdl_element_type)][int(keyopt_8)]
    except KeyError as exc:
        raise RuntimeError(
            f"Unsupported element type keyopt8 combination "
            f"Apdl Element Type: {apdl_element_type} "
            f"keyopt8: {keyopt_8}."
        ) from exc


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
        DPF MeshedRegion with lay-up information.
    name
        Analysis Ply Name
    """

    def __init__(self, mesh: MeshedRegion, name: str):
        """Initialize AnalysisPlyProvider."""
        self.name = name
        self.property_field = _get_analysis_ply(mesh, name)
        self._layer_indices = PropertyFieldIndexerNoDataPointer(self.property_field)

    def get_layer_index_by_element_id(self, element_id: int) -> Optional[np.int64]:
        """Get the layer index for the analysis ply in a given element.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        return self._layer_indices.by_id(element_id)

    def ply_element_ids(self) -> Sequence[np.int64]:
        """Return list of element labels of the analysis ply."""
        return cast(Sequence[np.int64], self.property_field.scoping.ids)


def get_dpf_material_id_by_analyis_ply_map(
    mesh: MeshedRegion,
    data_source_or_streams_provider: Union[DataSources, Operator],
) -> Dict[str, np.int64]:
    """Get Dict that maps analysis ply names to dpf_material_ids.

    Parameters
    ----------
    mesh
        DPF Meshed region enriched with lay-up information
    data_source_or_streams_provider:
        DPF data source with rst file or streams_provider. The streams provider is
        available from :attr:`.CompositeModel.core_model` (under metadata.streams_provider).
    """
    # Note: The stream_provider_or_data_source is not strictly needed for this workflow
    # We just need it because get_element_info_provider provider needs it (which needs
    # it to determine the keyopts, which are not needed in this context)
    # Maybe we could split the ElementInfoProvider
    analysis_ply_to_material_map = {}
    element_info_provider = get_element_info_provider(
        mesh=mesh, stream_provider_or_data_source=data_source_or_streams_provider
    )
    all_element_ids = mesh.elements.scoping.ids

    for analysis_ply_name in get_all_analysis_ply_names(mesh):
        analysis_ply_info_provider = AnalysisPlyInfoProvider(mesh, analysis_ply_name)

        # Note we check if there is any valid elements in this analysis ply
        # We won't find any elements if all the elements of a ply
        # were suppressed and therefore the analysis ply is not part
        # of the mesh anymore. In this case we simply don't
        # add the ply to the map
        diff = set(analysis_ply_info_provider.ply_element_ids()).intersection(all_element_ids)
        for element_id in diff:
            element_id_int = int(element_id)
            element_info = element_info_provider.get_element_info(element_id_int)
            if element_info is not None:
                layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(
                    element_id_int
                )
                assert (
                    layer_index is not None
                ), f"No layer index found for element with id {element_id_int}."
                analysis_ply_to_material_map[analysis_ply_name] = element_info.dpf_material_ids[
                    layer_index
                ]
                break

    return analysis_ply_to_material_map


def get_analysis_ply_index_to_name_map(
    mesh: MeshedRegion,
) -> Dict[int, str]:
    """Get Dict that maps analysis ply indices to analysis ply names.

    The resulting dict can be used to map from the indices stored in
    mesh.property_field("layer_to_analysis_ply") to the analysis ply name

    Parameters
    ----------
    mesh
        DPF Meshed region enriched with lay-up information
    """
    analysis_ply_name_to_index_map = {}
    with mesh.property_field("layer_to_analysis_ply").as_local_field() as local_field:
        for analysis_ply_name in get_all_analysis_ply_names(mesh):
            analysis_ply_property_field = _get_analysis_ply(
                mesh, analysis_ply_name, skip_check=True
            )
            first_element_id = analysis_ply_property_field.scoping.id(0)
            analysis_ply_indices: List[int] = local_field.get_entity_data_by_id(first_element_id)

            layer_index = analysis_ply_property_field.get_entity_data(0)[0]
            assert layer_index is not None
            analysis_ply_name_to_index_map[analysis_ply_indices[layer_index]] = analysis_ply_name

    return analysis_ply_name_to_index_map


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

        def get_indexer_with_data_pointer(field: PropertyField) -> PropertyFieldIndexerArrayValue:
            if no_bounds_checks:
                return PropertyFieldIndexerWithDataPointerNoBoundsCheck(field)
            else:
                return PropertyFieldIndexerWithDataPointer(field)

        def get_indexer_no_data_pointer(field: PropertyField) -> PropertyFieldIndexerSingleValue:
            if no_bounds_checks:
                return PropertyFieldIndexerNoDataPointerNoBoundsCheck(field)
            else:
                return PropertyFieldIndexerNoDataPointer(field)

        # Has to be always with bounds checks because it does not contain
        # data for all the elements
        self.layer_indices = PropertyFieldIndexerWithDataPointer(layer_indices)
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
        element_id:
            Element Id/Label

        Returns
        -------
        Optional[ElementInfo]:
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
        dpf_material_ids: Any = []
        element_type = self.dpf_element_types.by_id(element_id)
        if element_type is None:
            raise IndexError(f"No DPF element type for element with id {element_id}.")

        layer_data = self.layer_indices.by_id(element_id)
        if layer_data is not None:
            dpf_material_ids = self.layer_materials.by_id(element_id)
            assert dpf_material_ids is not None
            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True

        corner_nodes_dpf = self.corner_nodes_by_element_type[element_type]
        if corner_nodes_dpf < 0:
            raise ValueError(f"Invalid number of corner nodes for element with type {element_type}")
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
            dpf_material_ids=dpf_material_ids,
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
        keyopt_provider = dpf.Operator("mesh_property_provider")
        if isinstance(stream_provider_or_data_source, Operator):
            keyopt_provider.inputs.streams_container(stream_provider_or_data_source)
        else:
            keyopt_provider.inputs.data_sources(stream_provider_or_data_source)

        keyopt_provider.inputs.property_name(f"keyopt_{keyopt}")
        return keyopt_provider.outputs.property_as_property_field()

    requested_property_fields = [
        "apdl_element_type",
        "element_layer_indices",
        "element_layered_material_ids",
    ]

    for property_field_name in requested_property_fields:
        if property_field_name not in mesh.available_property_fields:
            message = f"Missing property field in mesh: '{property_field_name}'."
            if property_field_name in ["element_layer_indices", "element_layer_material_ids"]:
                message += (
                    " Maybe you have to run the lay-up provider operator first. "
                    "Please call add_layup_info_to_mesh "
                )
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


class LayupPropertiesProvider:
    """Provider for lay-up properties.

    Some properties such as layered dpf_material_ids and
    information about the element type are available
    through the :class:`~ElementInfoProvider`.

    Parameters
    ----------
    layup_provider:
        Use :func:`~add_layup_info_to_mesh` to obtain a lay-up provider.
    mesh
    """

    def __init__(self, layup_provider: Operator, mesh: MeshedRegion):
        """Initialize LayupProperties provider."""
        layup_outputs_container = layup_provider.outputs.section_data_container()
        composite_label = layup_outputs_container.labels[0]
        angle_field = layup_outputs_container.get_field({composite_label: LayupProperty.ANGLE})
        self._angle_indexer = FieldIndexerWithDataPointer(angle_field)
        thickness_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.THICKNESS}
        )
        self._thickness_indexer = FieldIndexerWithDataPointer(thickness_field)
        shear_angle_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.SHEAR_ANGLE}
        )
        self._shear_angle_indexer = FieldIndexerWithDataPointer(shear_angle_field)
        offset_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.LAMINATE_OFFSET}
        )
        self._offset_indexer = FieldIndexerNoDataPointer(offset_field)

        self._index_to_name_map = get_analysis_ply_index_to_name_map(mesh)

        self._analysis_ply_indexer = PropertyFieldIndexerWithDataPointer(
            mesh.property_field("layer_to_analysis_ply")
        )

    def get_layer_angles(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get angles for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._angle_indexer.by_id(element_id)

    def get_layer_thicknesses(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get thicknesses for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        return self._thickness_indexer.by_id(element_id)

    def get_layer_shear_angles(self, element_id: int) -> Optional[NDArray[np.double]]:
        """Get shear angle for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._shear_angle_indexer.by_id(element_id)

    def get_element_laminate_offset(self, element_id: int) -> Optional[np.double]:
        """Get laminate offset of element. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        return self._offset_indexer.by_id(element_id)

    def get_analysis_plies(self, element_id: int) -> Optional[Collection[str]]:
        """Get analysis ply names. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        indexes = self._analysis_ply_indexer.by_id(element_id)
        if indexes is None:
            return None
        return [self._index_to_name_map[index] for index in indexes]
