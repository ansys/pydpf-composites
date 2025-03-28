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
"""Protocol of Element Info Provider class."""
from dataclasses import dataclass
from typing import Any, Protocol

import ansys.dpf.core as dpf
from ansys.dpf.core import MeshedRegion, PropertyField
import numpy as np
from numpy.typing import NDArray

from .._indexer import get_property_field_indexer

# MAPDL element types that are supported by the ElementInfoProvider
_supported_mapdl_element_types = [181, 281, 185, 186, 187, 190]

# DPF Element types (for LS-Dyna) that are supported by the ElementInfoProvider
_supported_dpf_element_types = [
    dpf.element_types.Tet10,
    dpf.element_types.Hex8,
    dpf.element_types.Tet4,
    dpf.element_types.Pyramid5,
    dpf.element_types.Wedge6,
    dpf.element_types.Hex20,
    dpf.element_types.Pyramid13,
    dpf.element_types.Wedge15,
    dpf.element_types.TriShell3,
    dpf.element_types.QuadShell4,
    dpf.element_types.TriShell6,
    dpf.element_types.QuadShell8,
]


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
        Solver element type in case of MAPDL. For example, ``181`` for MAPDL's 4-node layered shell.
        DPF element type in case of LS-Dyna. For example, ``dpf.element_types.TriShell3``
        for LS-Dyna's 3-node shell.
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


class ElementInfoProviderProtocol(Protocol):
    """Protocol definition for ElementInfoProvider."""

    def get_element_info(self, element_id: int) -> ElementInfo | None:
        """Get :class:`~ElementInfo`."""


# Map of keyopt_8 to number of spots.
# Example: Element 181 with keyopt8==1 has two spots
_n_spots_by_element_type_and_keyopt_dict: dict[int, dict[int, int]] = {
    181: {0: 0, 1: 2, 2: 3},
    281: {0: 0, 1: 2, 2: 3},
    185: {0: 0, 1: 2},
    186: {0: 0, 1: 2},
    187: {0: 0},
    190: {0: 0, 1: 2},
}


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


def _is_shell(apdl_et: np.int64) -> bool:
    return {181: True, 281: True, 185: False, 186: False, 187: False, 190: False}[int(apdl_et)]


def _is_shell_dpf(dpf_et: dpf.element_types) -> bool:
    return dpf_et in [
        dpf.element_types.TriShell3,
        dpf.element_types.QuadShell4,
        dpf.element_types.TriShell6,
        dpf.element_types.QuadShell8,
    ]


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


class ElementInfoProvider(ElementInfoProviderProtocol):
    """Provider for :class:`~ElementInfo` for MAPDL models.

    Use :func:`~get_element_info_provider` to create :class:`~ElementInfoProvider`
    objects.

    Initialize the class before a loop and
    call :func:`~get_element_info` for each element.

    Note that the :class:`~ElementInfoProvider` class is not fully supported for
    distributed RST files. The :func:`~get_element_info` method will raise an
    exception if the DPF server version does not support reading the required
    information.

    Parameters
    ----------
    mesh
    layer_indices
    element_types_mapdl
    element_types_dpf
    keyopt_8_values
    keyopt_3_values
    material_ids
    solver_material_ids
    no_bounds_checks
        Disable bounds checks.
        Results in better performance but potentially cryptic
        error messages
    """

    def __init__(
        self,
        mesh: MeshedRegion,
        layer_indices: PropertyField,
        element_types_mapdl: PropertyField,
        element_types_dpf: PropertyField,
        keyopt_8_values: PropertyField,
        keyopt_3_values: PropertyField,
        material_ids: PropertyField,
        solver_material_ids: PropertyField | None = None,
        no_bounds_checks: bool = False,
    ):
        """Initialize ElementInfoProvider."""
        # Note: Every property we add to element info adds some performance
        # overhead for all the calls to get_element info. We should keep it
        # focused on the most important properties. We can add different providers
        # for other properties (such as thickness and angles)

        # Has to be always with bounds checks because it does not contain
        # data for all the elements

        self.layer_indices = get_property_field_indexer(layer_indices, no_bounds_checks)
        self.layer_materials = get_property_field_indexer(material_ids, no_bounds_checks)

        self.solver_element_types = get_property_field_indexer(
            element_types_mapdl, no_bounds_checks
        )
        self.dpf_element_types = get_property_field_indexer(element_types_dpf, no_bounds_checks)
        self.keyopt_8_values = get_property_field_indexer(keyopt_8_values, no_bounds_checks)
        self.keyopt_3_values = get_property_field_indexer(keyopt_3_values, no_bounds_checks)

        self.mesh = mesh
        self.corner_nodes_by_element_type = _get_corner_nodes_by_element_type_array()
        self.apdl_material_indexer = get_property_field_indexer(
            self.mesh.elements.materials_field, no_bounds_checks
        )

        self.solver_material_to_dpf_id: dict[int, int] = {}
        if solver_material_ids is not None:
            for dpf_mat_id in solver_material_ids.scoping.ids:
                mapdl_mat_ids = solver_material_ids.get_entity_data_by_id(dpf_mat_id)
                for mapdl_mat_id in mapdl_mat_ids:
                    self.solver_material_to_dpf_id[int(mapdl_mat_id)] = int(dpf_mat_id)

        self._element_info_cache: dict[int, ElementInfo | None] = {}

    def get_element_info(self, element_id: int) -> ElementInfo | None:
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
        if element_id in self._element_info_cache:
            return self._element_info_cache[element_id]

        is_layered = False
        n_layers = 1

        keyopt_8 = self.keyopt_8_values.by_id(element_id)
        keyopt_3 = self.keyopt_3_values.by_id(element_id)
        solver_element_type = self.solver_element_types.by_id(element_id)

        if keyopt_3 is None or keyopt_8 is None or solver_element_type is None:
            raise RuntimeError(
                "Could not determine element properties. Probably they were requested for an"
                f" invalid element id. Element id: {element_id}\n"
                "Note that creating ElementInfo is not fully supported for distributed RST files."
            )

        if int(solver_element_type) not in _supported_mapdl_element_types:
            self._element_info_cache[element_id] = None
            return None

        n_spots = _get_n_spots(solver_element_type, keyopt_8, keyopt_3)
        dpf_material_ids: Any = []
        element_type = self.dpf_element_types.by_id(element_id)
        if element_type is None:
            raise IndexError(f"No DPF element type for element with id {element_id}.")

        layer_data = self.layer_indices.by_id_as_array(element_id)
        if layer_data is not None:
            # can be of type int for single layer elements or array for multilayer materials
            dpf_material_ids = self.layer_materials.by_id_as_array(element_id)
            assert dpf_material_ids is not None
            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True
        elif self.solver_material_to_dpf_id:
            is_layered = False
            n_layers = 1
            mapdl_mat_id = self.apdl_material_indexer.by_id(element_id)
            if mapdl_mat_id:
                dpf_material_ids = np.array(
                    [self.solver_material_to_dpf_id[int(mapdl_mat_id)]], dtype=np.int64
                )
            else:
                raise RuntimeError(f"Could not evaluate material of element {element_id}.")

        corner_nodes_dpf = self.corner_nodes_by_element_type[element_type]
        if corner_nodes_dpf < 0:
            raise ValueError(f"Invalid number of corner nodes for element with type {element_type}")
        is_shell = _is_shell(solver_element_type)
        number_of_nodes_per_spot_plane = -1
        if is_layered:
            number_of_nodes_per_spot_plane = corner_nodes_dpf if is_shell else corner_nodes_dpf // 2

        element_info = ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=int(solver_element_type),
            dpf_material_ids=dpf_material_ids,
            id=element_id,
            is_shell=is_shell,
            number_of_nodes_per_spot_plane=number_of_nodes_per_spot_plane,
        )
        self._element_info_cache[element_id] = element_info

        return element_info


class ElementInfoProviderLSDyna(ElementInfoProviderProtocol):
    """Provider for :class:`~ElementInfo` for LSDyna models.

    Use :func:`~get_element_info_provider` to create :class:`~ElementInfoProvider`
    objects.

    Initialize the class before a loop and
    call :func:`~get_element_info` for each element.

    Parameters
    ----------
    mesh
    layer_indices
    element_types_dpf
    material_ids
    solver_material_ids
    no_bounds_checks
        Disable bounds checks.
        Results in better performance but potentially cryptic
        error messages
    """

    def __init__(
        self,
        mesh: MeshedRegion,
        layer_indices: PropertyField,
        element_types_dpf: PropertyField,
        material_ids: PropertyField,
        solver_material_ids: PropertyField,
        no_bounds_checks: bool = False,
    ):
        """Initialize ElementInfoProviderLSDyna."""
        # Note: Every property we add to element info adds some performance
        # overhead for all the calls to get_element info. We should keep it
        # focused on the most important properties. We can add different providers
        # for other properties (such as thickness and angles)

        # Has to be always with bounds checks because it does not contain
        # data for all the elements

        self.layer_indices = get_property_field_indexer(layer_indices, no_bounds_checks)
        self.layer_materials = get_property_field_indexer(material_ids, no_bounds_checks)

        self.dpf_element_types = get_property_field_indexer(element_types_dpf, no_bounds_checks)

        self.mesh = mesh
        self.corner_nodes_by_element_type = _get_corner_nodes_by_element_type_array()
        self.dyna_material_indexer = get_property_field_indexer(
            self.mesh.elements.materials_field, no_bounds_checks
        )

        self.solver_material_to_dpf_id = {}
        for dpf_mat_id in solver_material_ids.scoping.ids:
            mapdl_mat_ids = solver_material_ids.get_entity_data_by_id(dpf_mat_id)
            for mapdl_mat_id in mapdl_mat_ids:
                self.solver_material_to_dpf_id[mapdl_mat_id] = dpf_mat_id

        self._element_info_cache: dict[int, ElementInfo | None] = {}

    def get_element_info(self, element_id: int) -> ElementInfo | None:
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
        if element_id in self._element_info_cache:
            return self._element_info_cache[element_id]

        is_layered = False
        n_layers = 1

        dpf_element_type = self.dpf_element_types.by_id(element_id)

        if dpf_element_type is None:
            raise RuntimeError(
                "Could not determine element properties. Probably they were requested for an"
                f" invalid element id. Element id: {element_id}"
            )

        if dpf.element_types(dpf_element_type) not in _supported_dpf_element_types:
            self._element_info_cache[element_id] = None
            return None

        # LSDyna stores max 1 spot per element. It is assumed that this is the case
        n_spots = 1
        dpf_material_ids: Any = []

        layer_data = self.layer_indices.by_id_as_array(element_id)
        if layer_data is not None:
            # can be of type int for single layer elements or array for multilayer materials
            dpf_material_ids = self.layer_materials.by_id_as_array(element_id)
            assert dpf_material_ids is not None
            assert layer_data[0] + 1 == len(layer_data), "Invalid size of layer data"
            n_layers = layer_data[0]
            is_layered = True
        elif self.solver_material_to_dpf_id:
            is_layered = False
            n_layers = 1
            dyna_mat_id = self.dyna_material_indexer.by_id(element_id)
            if dyna_mat_id:
                dpf_material_ids = np.array(
                    [self.solver_material_to_dpf_id[dyna_mat_id]], dtype=np.int64
                )
            else:
                raise RuntimeError(f"Could not evaluate material of element {element_id}.")

        corner_nodes_dpf = self.corner_nodes_by_element_type[dpf_element_type]
        if corner_nodes_dpf < 0:
            raise ValueError(
                f"Invalid number of corner nodes for element with type {dpf_element_type}"
            )
        is_shell = _is_shell_dpf(dpf.element_types(dpf_element_type))
        number_of_nodes_per_spot_plane = -1
        if is_layered:
            # dyna stores only one result per spot plane
            number_of_nodes_per_spot_plane = 1

        element_info = ElementInfo(
            n_layers=n_layers,
            n_corner_nodes=corner_nodes_dpf,
            n_spots=n_spots,
            is_layered=is_layered,
            element_type=int(dpf_element_type),
            dpf_material_ids=dpf_material_ids,
            id=element_id,
            is_shell=is_shell,
            number_of_nodes_per_spot_plane=number_of_nodes_per_spot_plane,
        )
        self._element_info_cache[element_id] = element_info

        return element_info
