"""Functions to get elementary indices based on filter input."""
from typing import Collection, Optional

import numpy as np
from numpy.typing import NDArray

from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, ElementInfo


# Todo: Implement using numpy
def get_selected_indices(
    element_info: ElementInfo,
    layers: Optional[Collection[int]] = None,
    nodes: Optional[Collection[int]] = None,
    spots: Optional[Collection[int]] = None,
    disable_checks: bool = False,
) -> NDArray[np.int64]:
    """Return the elementary indices based on selected layers, corner_nodes, spots and ElementInfo.

    Returns an empty selection if any of the collections is empty.

    :param element_info: ElementInfo
    :param layers: List of selected layers
    :param nodes: List of selected nodes
    :param spots:  List of selected spots
                   The spot indices correspond to
                        0: bot, 1: top         if element_info.n_spots == 2
                        0: bot, 1: top  2: mid if element_info.n_spots == 3

    :param disable_checks:  Set to True to disable checks.
           Results in better performance but potentially
           cryptic error messages or invalid indices
    :return: numpy array of selected indices
    """
    if layers is None:
        layer_indices: Collection[int] = range(element_info.n_layers)
    else:
        if len(layers) == 0:
            return np.array([])
        layer_indices = layers

    if nodes is None:
        node_indices: Collection[int] = range(element_info.nodes_per_layer)
    else:
        if len(nodes) == 0:
            return np.array([])
        node_indices = nodes
    if spots is None:
        spot_indices: Collection[int] = range(element_info.n_spots)
    else:
        if len(spots) == 0:
            return np.array([])
        spot_indices = spots

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

        if max(node_indices) >= element_info.nodes_per_layer:
            raise RuntimeError(
                f"corner node index {max(node_indices)} is greater or "
                f"equal number of corner nodes {element_info.nodes_per_layer}. "
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


def get_selected_indices_by_material_id(
    element_info: ElementInfo, material_id: int
) -> NDArray[np.int64]:
    """Get selected indices by material id.

    Selects all indices that are in a layer with the given material
    :param element_info: ElementInfo
    :param material_id
    :return: elementary indices
    """
    layer_indices = [
        index for index, mat_id in enumerate(element_info.material_ids) if mat_id == material_id
    ]
    return get_selected_indices(element_info, layers=layer_indices)


def get_selected_indices_by_analysis_ply(
    analysis_ply_info_provider: AnalysisPlyInfoProvider, element_info: ElementInfo
) -> NDArray[np.int64]:
    """Get selected indices by analysis ply.

    Selects all indices that are in a layer with the given analysis ply
    :param analysis_ply_info_provider: The AnalysisPlyInfoProvider for the Analysis ply.
    :param element_info: ElementInfo
    :return: elementary indices
    """
    layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(element_info.id)
    if layer_index is None:
        raise RuntimeError(
            f"Analysis Ply '{analysis_ply_info_provider.name}' "
            f"is not part of element {element_info.id}"
        )
    else:
        return get_selected_indices(element_info, layers=[int(layer_index)])
