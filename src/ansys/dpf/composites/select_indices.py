import numpy as np
from typings import List, Optional

from ansys.dpf.composites.layup_info import ElementInfo


# Todo: Implement using numpy
def get_selected_indices(
    element_info: ElementInfo,
    layers: Optional[List[int]] = None,
    corner_nodes: Optional[List[int]] = None,
    spots: Optional[List[int]] = None,
) -> List[int]:
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


def get_selected_indices_by_material_id(element_info: ElementInfo, material_id: int) -> List[int]:
    layer_indices = [
        index for index, mat_id in enumerate(element_info.material_ids) if mat_id == material_id
    ]
    return get_selected_indices(element_info, layers=layer_indices)
