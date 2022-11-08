"""Functions to get elementary indices based on filter input."""
from typing import Collection, Optional

import numpy as np
from numpy.typing import NDArray

from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, ElementInfo


# Todo: Implement using numpy
# Todo implement bound checks
def get_selected_indices(
    element_info: ElementInfo,
    layers: Optional[Collection[int]] = None,
    corner_nodes: Optional[Collection[int]] = None,
    spots: Optional[Collection[int]] = None,
) -> NDArray[np.int64]:
    """Return the elementary indices based on selected layers, corner_nodes, spots and ElementInfo.

    :param element_info: ElementInfo
    :param layers: List of selected layers
    :param corner_nodes: List of selected nodes
    :param spots:  List of selected spots
    :return: numpy array of selected indices
    """
    if layers is None:
        layer_indices: Collection[int] = range(element_info.n_layers)
    else:
        layer_indices = layers

    if corner_nodes is None:
        corner_node_indices: Collection[int] = range(element_info.n_corner_nodes)
    else:
        corner_node_indices = corner_nodes
    if spots is None:
        spot_indices: Collection[int] = range(element_info.n_spots)
    else:
        spot_indices = spots

    all_indices = np.zeros(
        len(spot_indices) * len(corner_node_indices) * len(layer_indices), dtype=np.int64
    )
    # Todo: Use numpy. Probably use ravel_multi_index
    current_index = 0
    for layer_index in layer_indices:
        layer_start_index = layer_index * element_info.n_corner_nodes * element_info.n_spots
        for spot_index in spot_indices:
            spot_start_index = layer_start_index + spot_index * element_info.n_corner_nodes
            for corner_index in corner_node_indices:
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
    return get_selected_indices(element_info, layers=[layer_index])
