# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

from collections.abc import Sequence

try:
    from ansys.dpf.core.common import locations
except ImportError:
    # support ansys.dpf.core < 0.13
    from ansys.dpf.gate.common import locations
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import Sym3x3TensorComponent
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.server_helpers import version_equal_or_later

from .helper import get_basic_shell_files


def get_reduced_value(all_spot_values: Sequence[float], reduction_strategy: SpotReductionStrategy):
    if reduction_strategy == SpotReductionStrategy.AVG:
        return sum(all_spot_values) / len(all_spot_values)
    if reduction_strategy == SpotReductionStrategy.MIN:
        return min(all_spot_values)
    if reduction_strategy == SpotReductionStrategy.MAX:
        return max(all_spot_values)
    if reduction_strategy == SpotReductionStrategy.BOT:
        return all_spot_values[0]
    if reduction_strategy == SpotReductionStrategy.MID:
        return all_spot_values[2]
    if reduction_strategy == SpotReductionStrategy.TOP:
        return all_spot_values[1]
    raise ValueError(f"Unknown reduction strategy: {reduction_strategy}")


ALL_REDUCTION_STRATEGIES = [
    SpotReductionStrategy.AVG,
    SpotReductionStrategy.MIN,
    SpotReductionStrategy.MAX,
    SpotReductionStrategy.BOT,
    SpotReductionStrategy.MID,
    SpotReductionStrategy.TOP,
]

ALL_TENSOR_COMPONENTS = [
    Sym3x3TensorComponent.TENSOR11,
    Sym3x3TensorComponent.TENSOR22,
    Sym3x3TensorComponent.TENSOR22,
    Sym3x3TensorComponent.TENSOR21,
    Sym3x3TensorComponent.TENSOR31,
    Sym3x3TensorComponent.TENSOR32,
]


def get_all_spot_values_first_element_first_node(stress_field, component=0):
    all_spot_values = []
    entity_data = stress_field.get_entity_data_by_id(1)[:, component]
    number_of_nodes = 4
    for spot_index in range(3):
        all_spot_values.append(entity_data[spot_index * number_of_nodes])
    return all_spot_values


def test_get_ply_wise_data(dpf_server):
    if not version_equal_or_later(dpf_server, "8.0"):
        return
    files = get_basic_shell_files()

    composite_model = CompositeModel(files, server=dpf_server)

    stress_result_op = composite_model.core_model.results.stress()
    stress_result_op.inputs.bool_rotate_to_global(False)
    stress_field = stress_result_op.outputs.fields_container()[0]

    first_ply = "P1L1__woven_45"

    element_id = 1
    first_node_index = 0

    for component in ALL_TENSOR_COMPONENTS:
        for reduction_strategy in ALL_REDUCTION_STRATEGIES:
            all_spot_values = get_all_spot_values_first_element_first_node(
                stress_field, component=component.value
            )

            elemental_nodal_data = get_ply_wise_data(
                stress_field,
                first_ply,
                composite_model.get_mesh(),
                component=component,
                spot_reduction_strategy=reduction_strategy,
            )

            assert len(elemental_nodal_data.scoping.ids) == 4
            assert len(elemental_nodal_data.get_entity_data_by_id(element_id)) == 4
            assert elemental_nodal_data.location == locations.elemental_nodal

            assert np.allclose(
                elemental_nodal_data.get_entity_data_by_id(element_id)[first_node_index],
                get_reduced_value(all_spot_values, reduction_strategy),
            )

            elemental_data = get_ply_wise_data(
                stress_field,
                first_ply,
                composite_model.get_mesh(),
                component=component,
                spot_reduction_strategy=reduction_strategy,
                requested_location=locations.elemental,
            )
            assert len(elemental_data.scoping.ids) == 4
            assert len(elemental_data.get_entity_data_by_id(element_id)) == 1
            assert elemental_data.location == locations.elemental

            assert np.allclose(
                elemental_data.get_entity_data_by_id(element_id)[first_node_index],
                sum(elemental_nodal_data.get_entity_data_by_id(element_id)) / 4,
            )

            nodal_data = get_ply_wise_data(
                stress_field,
                first_ply,
                composite_model.get_mesh(),
                component=component,
                spot_reduction_strategy=reduction_strategy,
                requested_location=locations.nodal,
            )
            assert len(nodal_data.scoping.ids) == 9
            assert len(nodal_data.get_entity_data_by_id(element_id)) == 1
            assert nodal_data.location == locations.nodal

            # Select node that only belongs to element 1
            # no averaging needed
            node_index_with_no_neighbours = 1
            first_node_index_of_element_1 = (
                composite_model.get_mesh().elements.connectivities_field.get_entity_data_by_id(
                    element_id
                )[node_index_with_no_neighbours]
            )
            node_id_to_index = composite_model.get_mesh().nodes.mapping_id_to_index
            node_id = list(node_id_to_index.keys())[
                list(node_id_to_index.values()).index(first_node_index_of_element_1)
            ]

            assert np.allclose(
                nodal_data.get_entity_data_by_id(node_id)[0],
                elemental_nodal_data.get_entity_data_by_id(element_id)[
                    node_index_with_no_neighbours
                ],
            )
