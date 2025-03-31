# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Lay-up information provider."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import cast
from warnings import warn

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, MeshedRegion, Operator, PropertyField
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .._indexer import get_field_indexer, get_property_field_indexer
from ..constants import SolverType
from ..server_helpers import version_equal_or_later, version_older_than
from ._element_info import (
    ElementInfoProvider,
    ElementInfoProviderLSDyna,
    ElementInfoProviderProtocol,
)
from ._enums import LayupProperty


def _get_separator(server: BaseServer) -> str:
    if version_older_than(server, "7.0"):
        return ":"
    else:
        return "::"


def _get_analysis_ply_prefix(server: BaseServer) -> str:
    return "AnalysisPly" + _get_separator(server)


def get_all_analysis_ply_names(mesh: MeshedRegion) -> Collection[str]:
    """Get names of all available analysis plies."""
    prefix = _get_analysis_ply_prefix(mesh._server)  # pylint: disable=protected-access
    return [
        property_field_name[len(prefix) :]
        for property_field_name in mesh.available_property_fields
        if property_field_name.startswith(prefix)
    ]


def _get_analysis_ply(mesh: MeshedRegion, name: str, skip_check: bool = False) -> PropertyField:
    prefix = _get_analysis_ply_prefix(mesh._server)  # pylint: disable=protected-access
    property_field_name = prefix + name

    # Because this test can be slow, it can be skipped
    if not skip_check and property_field_name not in mesh.available_property_fields:
        available_analysis_plies = get_all_analysis_ply_names(mesh)
        raise RuntimeError(
            f"Analysis ply is not available: {name}. "
            f"Available analysis plies: {available_analysis_plies}"
        )
    return mesh.property_field(property_field_name)


def _get_layup_model_context(layup_provider: dpf.Operator) -> int:
    """Get the lay-up model context from the lay-up provider."""
    return cast(int, layup_provider.get_output(218, int))


#  Note: Must be in sync with the ``LayupModelContextTypeEnum`` object in the C++ code.
class LayupModelContextType(Enum):
    """Type of the lay-up information."""

    NOT_AVAILABLE = 0  # no layup data
    ACP = 1  # lay-up data was read from ACP
    RST = 2  # lay-up data was read from RST
    MIXED = 3  # lay-up data was read from RST and ACP


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
_n_spots_by_element_type_and_keyopt_dict: dict[int, dict[int, int]] = {
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
        (
            dpf.element_types.descriptor(element_type).n_corner_nodes
            if dpf.element_types.descriptor(element_type).n_corner_nodes is not None
            else -1
        )
        for element_type in all_element_types
    ]
    return corner_nodes_by_element_type


@dataclass(frozen=True)
class AnalysisPlyInfo:
    """Data about an analysis ply."""

    angle: float
    global_ply_number: int
    id: str
    material_name: str
    nominal_thickness: float


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
        self._layer_indices = get_property_field_indexer(self.property_field, False)

    def get_layer_index_by_element_id(self, element_id: int) -> np.int64 | None:
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

    def basic_info(self) -> AnalysisPlyInfo:
        """Get data such as material, angle etc. of the analysis ply."""
        # Extract information from property field
        properties_op = dpf.Operator("composite::get_field_properties_operator")
        properties_op.inputs.field(self.property_field)
        # returns a DataTree object
        properties = properties_op.outputs.properties()
        as_dict = properties.to_dict()

        return AnalysisPlyInfo(
            float(as_dict["analysis_ply_design_angle"]),
            int(as_dict["global_ply_id"]),
            self.name,
            as_dict["material_name"],
            float(as_dict["nominal_thickness"]),
        )


def get_dpf_material_id_by_analyis_ply_map(
    mesh: MeshedRegion,
    data_source_or_streams_provider: DataSources | Operator,
) -> dict[str, np.int64]:
    """Get Dict that maps analysis ply names to dpf_material_ids.

    Parameters
    ----------
    mesh
        DPF Meshed region enriched with lay-up information
    data_source_or_streams_provider:
        DPF data source with rst file or streams_provider. The streams provider is
        available from :attr:`.CompositeModel.core_model` (under metadata.streams_provider).

    Notes
    -----
    Cache the output because the computation can be performance-critical.
    """
    warn(
        "`get_dpf_material_id_by_analyis_ply_map` is deprecated. "
        " and was replaced by `get_dpf_material_id_by_analysis_ply_map`.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return get_dpf_material_id_by_analysis_ply_map(mesh, data_source_or_streams_provider)


# todo: pass solver type
def get_dpf_material_id_by_analysis_ply_map(
    mesh: MeshedRegion,
    data_source_or_streams_provider: DataSources | Operator,
    solver_type: SolverType = SolverType.MAPDL,
) -> dict[str, np.int64]:
    """Get the dictionary that maps analysis ply names to DPF material IDs.

    Parameters
    ----------
    mesh
        DPF Meshed region enriched with lay-up information
    data_source_or_streams_provider:
        DPF data source with RST file or streams provider. The streams provider is
        available from the :attr:`.CompositeModel.core_model` attribute
        (under ``metadata.streams_provider``).
    solver_type:
        Type of result file (model). The default is ``SolverType.MAPDL``.

    Note
    ----
    Cache the output because the computation can be performance-critical.
    """
    # Note: The stream_provider_or_data_source is not strictly needed for this workflow
    # We just need it because get_element_info_provider provider needs it (which needs
    # it to determine the keyopts, which are not needed in this context)
    # Maybe we could split the ElementInfoProvider
    analysis_ply_to_material_map = {}
    element_info_provider = get_element_info_provider(
        mesh=mesh,
        stream_provider_or_data_source=data_source_or_streams_provider,
        solver_type=solver_type,
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
) -> dict[int, str]:
    """Get Dict that maps analysis ply indices to analysis ply names.

    The resulting dict can be used to map from the indices stored in
    mesh.property_field("layer_to_analysis_ply") to the analysis ply name

    Parameters
    ----------
    mesh
        DPF Meshed region enriched with lay-up information

    .. note::

        Analysis plies of ACP's imported solid model that are linked only
        to homogeneous elements are currently skipped.
    """
    analysis_ply_name_to_index_map = {}
    with mesh.property_field("layer_to_analysis_ply").as_local_field() as local_field:
        element_ids = local_field.scoping.ids
        for analysis_ply_name in get_all_analysis_ply_names(mesh):
            analysis_ply_property_field = _get_analysis_ply(
                mesh, analysis_ply_name, skip_check=True
            )
            first_element_id = analysis_ply_property_field.scoping.id(0)
            # analysis plies which represent a filler ply are ignored because
            # they are linked to homogeneous elements only. So, they are not
            # part of layer_to_analysis_ply. This filler plies can occur in
            # imported solid models.
            # The analysis ply indices can be retrieved from
            # analysis_ply_property_field as soon as the
            # properties of PropertyField are available in Python.
            if first_element_id not in element_ids:
                continue

            analysis_ply_indices: list[int] = local_field.get_entity_data_by_id(first_element_id)

            layer_index = analysis_ply_property_field.get_entity_data(0)[0]
            assert layer_index is not None
            analysis_ply_name_to_index_map[analysis_ply_indices[layer_index]] = analysis_ply_name

    return analysis_ply_name_to_index_map


def get_element_info_provider(
    mesh: MeshedRegion,
    stream_provider_or_data_source: Operator | DataSources,
    material_provider: Operator | None = None,
    no_bounds_checks: bool = False,
    solver_type: SolverType = SolverType.MAPDL,
) -> ElementInfoProviderProtocol:
    """Get :class:`~ElementInfoProvider` Object.

    Parameters
    ----------
    mesh
    stream_provider_or_data_source
        dpf stream provider or dpf data source
    material_provider
        DPF operator that provides material information.
    no_bounds_checks
        Disable bounds checks. Improves
        performance but can result in cryptic error messages
    solver_type
        Specify the type of solver (MAPDL or LSDyna).

    Returns
    -------
    ElementInfoProvider

    Notes
    -----
        Either a data_source or a stream_provider is required
    """

    def _check_existence_of_property_fields(requested_property_fields: list[str]) -> None:
        for property_field_name in requested_property_fields:
            if property_field_name not in mesh.available_property_fields:
                message = f"Missing property field in mesh: '{property_field_name}'."
                if property_field_name in ["element_layer_indices", "element_layer_material_ids"]:
                    message += (
                        " Maybe you have to run the lay-up provider operator first. "
                        "Please call add_layup_info_to_mesh "
                    )
                raise RuntimeError(message)

    if solver_type == SolverType.LSDYNA:
        if version_older_than(mesh._server, "10.0"):  # pylint: disable=protected-access
            raise RuntimeError("LSDyna support is only available in DPF 10.0 (2025 R2) and later.")

        _check_existence_of_property_fields(
            [
                "element_layer_indices",
                "element_layered_material_ids",
                "eltype",
            ]
        )

        helper_op = dpf.Operator("composite::materials_container_helper")
        if material_provider is None:
            raise RuntimeError("Material provider is required for LSDyna data.")
        helper_op.inputs.materials_container(material_provider.outputs)
        solver_material_ids = helper_op.outputs.solver_material_ids()

        fields = {
            "layer_indices": mesh.property_field("element_layer_indices"),
            "element_types_dpf": mesh.elements.element_types_field,
            "material_ids": mesh.property_field("element_layered_material_ids"),
            "solver_material_ids": solver_material_ids,
        }

        return ElementInfoProviderLSDyna(mesh, **fields, no_bounds_checks=no_bounds_checks)
    else:

        def get_keyopt_property_field(keyopt: int) -> PropertyField:
            keyopt_provider = dpf.Operator("mesh_property_provider")
            if isinstance(stream_provider_or_data_source, Operator):
                keyopt_provider.inputs.streams_container(stream_provider_or_data_source)
            else:
                keyopt_provider.inputs.data_sources(stream_provider_or_data_source)

            keyopt_provider.inputs.property_name(f"keyopt_{keyopt}")
            return keyopt_provider.outputs.property_as_property_field()

        _check_existence_of_property_fields(
            [
                "element_layer_indices",
                "element_layered_material_ids",
                "apdl_element_type",
            ]
        )

        # pylint: disable=protected-access
        if material_provider and version_equal_or_later(mesh._server, "8.0"):
            helper_op = dpf.Operator("composite::materials_container_helper")
            helper_op.inputs.materials_container(material_provider.outputs)
            solver_material_ids = helper_op.outputs.solver_material_ids()
        else:
            solver_material_ids = None

        fields = {
            "layer_indices": mesh.property_field("element_layer_indices"),
            "element_types_mapdl": mesh.property_field("apdl_element_type"),
            "element_types_dpf": mesh.elements.element_types_field,
            "keyopt_8_values": get_keyopt_property_field(8),
            "keyopt_3_values": get_keyopt_property_field(3),
            "material_ids": mesh.property_field("element_layered_material_ids"),
            "solver_material_ids": solver_material_ids,
        }

        return ElementInfoProvider(mesh, **fields, no_bounds_checks=no_bounds_checks)


def get_material_names_to_dpf_material_index(
    material_container_helper_op: dpf.Operator,
) -> dict[str, int]:
    """Get a dictionary that maps material names to DPF material IDs."""
    if material_container_helper_op is None:
        raise RuntimeError(
            "The used DPF server does not support the requested data. "
            "Use version 2024 R1-pre0 or later."
        )

    string_field = material_container_helper_op.outputs.material_names()
    material_ids = string_field.scoping.ids

    names = {}
    for dpf_mat_id in material_ids:
        names[string_field.data[string_field.scoping.index(dpf_mat_id)]] = dpf_mat_id

    return names


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
        self._angle_indexer = get_field_indexer(angle_field)
        thickness_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.THICKNESS}
        )
        self._thickness_indexer = get_field_indexer(thickness_field)
        shear_angle_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.SHEAR_ANGLE}
        )
        self._shear_angle_indexer = get_field_indexer(shear_angle_field)
        offset_field = layup_outputs_container.get_field(
            {composite_label: LayupProperty.LAMINATE_OFFSET}
        )
        self._offset_indexer = get_field_indexer(offset_field)

        self._index_to_name_map = get_analysis_ply_index_to_name_map(mesh)

        self._analysis_ply_indexer = get_property_field_indexer(
            mesh.property_field("layer_to_analysis_ply"), False
        )

    def get_layer_angles(self, element_id: int) -> NDArray[np.double] | None:
        """Get angles for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._angle_indexer.by_id_as_array(element_id)

    def get_layer_thicknesses(self, element_id: int) -> NDArray[np.double] | None:
        """Get thicknesses for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        return self._thickness_indexer.by_id_as_array(element_id)

    def get_layer_shear_angles(self, element_id: int) -> NDArray[np.double] | None:
        """Get shear angle for all layers. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._shear_angle_indexer.by_id_as_array(element_id)

    def get_element_laminate_offset(self, element_id: int) -> np.double | None:
        """Get laminate offset of element. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        return self._offset_indexer.by_id(element_id)

    def get_analysis_plies(self, element_id: int) -> Sequence[str] | None:
        """Get analysis ply names. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label

        """
        indices = self._analysis_ply_indexer.by_id_as_array(element_id)
        if indices is None:
            return None
        return [self._index_to_name_map[index] for index in indices]
