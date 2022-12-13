"""Functions to get elementary indices based on filter input."""
from typing import Collection, Optional

import numpy as np
from numpy.typing import NDArray

from ansys.dpf.composites import Spot
from ansys.dpf.composites.enums import get_rst_spot_index
from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, ElementInfo


def get_selected_indices(
    element_info: ElementInfo,
    layers: Optional[Collection[int]] = None,
    nodes: Optional[Collection[int]] = None,
    spots: Optional[Collection[Spot]] = None,
    disable_checks: bool = False,
) -> NDArray[np.int64]:
    """Return the elementary indices based on selected layers, corner_nodes, spots and ElementInfo.

    Parameters
    ----------
    element_info
    layers
        List of selected layers.
    nodes
        List of selected nodes
    spots
        List of selected spots.
    disable_checks:
        Set to True to disable checks.
        Results in better performance but potentially
        cryptic error messages or invalid indices

    Returns
    -------
    NDArray:
        Array of selected indices


    Notes
    -----
    Returns an empty selection if any of the collections is empty.
    """
    if layers is None:
        layer_indices: Collection[int] = range(element_info.n_layers)
    else:
        if len(layers) == 0:
            return np.array([])
        layer_indices = layers

    if nodes is None:
        node_indices: Collection[int] = range(element_info.number_of_nodes_per_spot_plane)
    else:
        if len(nodes) == 0:
            return np.array([])
        node_indices = nodes
    if spots is None:
        spot_indices: Collection[int] = range(element_info.n_spots)
    else:
        if len(spots) == 0:
            return np.array([])
        spot_indices = [get_rst_spot_index(spot) for spot in spots]

    if not disable_checks:
        if not element_info.is_layered:
            raise RuntimeError("Computation of indices is not supported for non-layered elements.")
        if element_info.n_spots == 0:
            raise RuntimeError(
                "Computation of indices is not supported for elements with no spots. This could"
                "mean this is a output has only been written at the bottom and "
                f"the top of the stack of layers. Element Info: {element_info}"
            )
        if max(layer_indices) >= element_info.n_layers:
            raise RuntimeError(
                f"Layer index {max(layer_indices)} is greater or "
                f"equal number of layers {element_info.n_layers}. Element Info: {element_info}"
            )

        if max(node_indices) >= element_info.number_of_nodes_per_spot_plane:
            raise RuntimeError(
                f"corner node index {max(node_indices)} is greater or "
                f"equal number of corner nodes {element_info.number_of_nodes_per_spot_plane}. "
                f"Element Info: {element_info}"
            )

        if max(spot_indices) >= element_info.n_spots:
            raise RuntimeError(
                f"spot index {max(spot_indices)} is greater or "
                f"equal number of spots {element_info.n_spots}. Element Info: {element_info}"
            )

    all_indices = np.zeros(
        len(spot_indices) * len(node_indices) * len(layer_indices), dtype=np.int64
    )
    # Todo: Use numpy. Probably use ravel_multi_index
    current_index = 0
    for layer_index in layer_indices:
        layer_start_index = layer_index * element_info.n_corner_nodes * element_info.n_spots
        for spot_index in spot_indices:
            spot_start_index = layer_start_index + spot_index * element_info.n_corner_nodes
            for corner_index in node_indices:
                all_indices[current_index] = spot_start_index + corner_index
                current_index = current_index + 1

    return all_indices


def get_selected_indices_by_dpf_material_ids(
    element_info: ElementInfo, dpf_material_ids: Collection[np.int64]
) -> NDArray[np.int64]:
    """Get selected indices by dpf_material_ids.

    Selects all indices that are in a layer with one of the selected materials

    Parameters
    ----------
    element_info: ElementInfo
    dpf_material_ids
        Collection of dpf_material_ids to select

    Returns
    -------
    NDArray[int64]:
        Selected elementary indices

    """
    layer_indices = [
        index
        for index, mat_id in enumerate(element_info.dpf_material_ids)
        if mat_id in dpf_material_ids
    ]
    return get_selected_indices(element_info, layers=layer_indices)


def get_selected_indices_by_analysis_ply(
    analysis_ply_info_provider: AnalysisPlyInfoProvider, element_info: ElementInfo
) -> NDArray[np.int64]:
    """Get selected indices by analysis ply.

    Selects all indices that are in a layer with the given analysis ply

    Parameters
    ----------
    analysis_ply_info_provider: AnalysisPlyInfoProvider
        The AnalysisPlyInfoProvider for the Analysis ply.
    element_info: ElementInfo

    Returns
    -------
    NDArray[int64]:
        selected elementary indices
    """
    layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(element_info.id)
    if layer_index is None:
        raise RuntimeError(
            f"Analysis Ply '{analysis_ply_info_provider.name}' "
            f"is not part of element {element_info.id}"
        )
    else:
        return get_selected_indices(element_info, layers=[int(layer_index)])
