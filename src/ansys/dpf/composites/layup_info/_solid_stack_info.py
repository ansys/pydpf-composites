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

from dataclasses import dataclass
from collections.abc import Sequence
import numpy as np

from ansys.dpf.composites.layup_info import ElementInfoProvider
import ansys.dpf.core as dpf
from ansys.dpf.core import MeshedRegion

from ansys.dpf.composites.constants import Spot
from ansys.dpf.composites.failure_criteria import FailureModeEnum
from ansys.dpf.composites.layup_info import LayupPropertiesProvider

from ..sampling_point_types import FailureResult
from ..select_indices import get_selected_indices

MAX_RESERVE_FACTOR = 1000.0
SOLID_SPOTS = [Spot.BOTTOM, Spot.TOP]

def _irf2rf(irf):
    if irf == 0.0:
        return MAX_RESERVE_FACTOR

    rf = 1.0 / irf
    return min(rf, MAX_RESERVE_FACTOR)


def _irf2mos(irf):
    rf = _irf2rf(irf)
    return rf - 1.0


# todo: check what happens if the stack has drop-off elements (w/o analysis plies)

@dataclass(frozen=True)
class SolidStack:
    # list of solid element labels ordered from the bottom to the top
    element_ids: Sequence[int]
    # list of analysis plies for each solid element in the stack
    element_wise_analysis_plies: dict[int, Sequence[str]]
    element_ply_thicknesses: dict[int, Sequence[float]]

    @property
    def num_elements(self):
        return len(self.element_ids)

    @property
    def analysis_ply_ids_and_thicknesses(self):
        res = []
        for e_id in self.element_ids:
            for index, ply_id in enumerate(self.element_wise_analysis_plies[e_id]):
                res.append((ply_id, self.element_ply_thicknesses[e_id][index]))

        return res

    @property
    def number_of_analysis_plies(self):
        return len(self.analysis_ply_ids_and_thicknesses)


class SolidStackProvider:

    SOLID_STACK_PROPERTY_FIELD_NAME = "solid_stacks"

    def __init__(self, mesh: MeshedRegion, layup_property_provider: LayupPropertiesProvider):
        self._mesh = mesh
        self._layup_property_provider = layup_property_provider
        if self.SOLID_STACK_PROPERTY_FIELD_NAME not in self._mesh.available_property_fields:
            raise RuntimeError(
                f"Property field '{self.SOLID_STACK_PROPERTY_FIELD_NAME}' not found in mesh."
                " Please make sure the layup provider has been executed."
            )

        self._solid_stacks_property_field = self._mesh.property_field(
            self.SOLID_STACK_PROPERTY_FIELD_NAME
        )

        self._element_id_to_solid_stack_index_map = {}
        self._solid_stacks: list[SolidStack] = []
        # prepare solid stack info
        self._prepare_data()

    @property
    def number_of_stacks(self):
        return self._solid_stacks_property_field.scoping.size

    @property
    def solid_stacks(self):
        """All solid stacks in the mesh."""
        return self._solid_stacks

    def _prepare_data(self):
        for index in range(0, self.number_of_stacks):
            elementary_data = self._solid_stacks_property_field.get_entity_data(index)
            element_ids = []
            element_wise_analysis_plies: dict[int, Sequence[str]] = {}
            element_ply_thicknesses: dict[int, Sequence[float]] = {}
            for element_id, level in elementary_data:
                ply_ids = self._layup_property_provider.get_analysis_plies(element_id)
                if ply_ids:
                    # only proces elements with plies
                    element_ids.append(int(element_id))
                    element_wise_analysis_plies[element_id] = ply_ids
                    self._element_id_to_solid_stack_index_map[element_id] = len(self._solid_stacks)
                    element_ply_thicknesses[int(element_id)] = (
                        self._layup_property_provider.get_layer_thicknesses(element_id)
                    )

            self._solid_stacks.append(
                SolidStack(
                    element_ids=element_ids,
                    element_wise_analysis_plies=element_wise_analysis_plies,
                    element_ply_thicknesses=element_ply_thicknesses,
                )
            )

    def get_solid_stack(self, element_id: int) -> SolidStack | None:
        """Get the full solid stack for a given element.

        Returns None if the element is not part of a solid stack.
        """
        if element_id in self._element_id_to_solid_stack_index_map:
            solid_stack_index = self._element_id_to_solid_stack_index_map[element_id]
            return self._solid_stacks[solid_stack_index]
        return None

    def get_solid_stacks(self, element_ids: any) -> list[SolidStack]:
        """Get unique list of solid stacks for a list of element ids."""
        processed_elements: list[int] = []
        selected_stacks: list[SolidStack] = []
        for e_id in element_ids:
            stack = self.get_solid_stack(e_id)
            if stack:
                if stack.element_ids[0] in processed_elements:
                    # it's enough to check if the first element of the stack is already processed
                    continue
                else:
                    selected_stacks.append(stack)
                    processed_elements.extend(stack.element_ids)
        return selected_stacks


def get_through_the_thickness_failure_results(
    solid_stack: SolidStack,
    element_info_provider: ElementInfoProvider,
    irf_field: dpf.Field,
    failure_mode_field: dpf.Field,
) -> list[FailureResult]:
    """
    Get through-the-thickness failure results of the solid stack.

    The maximum IRF is extracted at the bottom and top of each ply for each element in the stack.
    The result contains the failure mode, IRF, reserve factor and margin of safety for each spot and ply.
    The inputs irf_field and failure_mode_field are expected to have location element_nodal
    (no data reduction) with data at the bottom and top of each layer (ply).

    Example:
        failures = get_through_the_thickness_failure_results(stack, element_info_provider, irf_field, failure_mode_field)
    """
    failure_results = []

    for element_index, element_id in enumerate(solid_stack.element_ids):
        this_element_irfs = irf_field.get_entity_data_by_id(element_id)
        this_element_modes = failure_mode_field.get_entity_data_by_id(element_id)

        plies = solid_stack.element_wise_analysis_plies[element_id]
        element_info = element_info_provider.get_element_info(element_id)
        for ply_index, ply_id in enumerate(plies):
            # select all data points of the ply / layer for each spot separately
            for spot in SOLID_SPOTS:

                selected_indices = get_selected_indices(
                    element_info, layers=[ply_index], nodes=None, spots=[spot]
                )
                spot_wise_irfs = this_element_irfs[selected_indices]
                index_of_max = spot_wise_irfs.argmax()
                spot_wise_modes = this_element_modes[selected_indices]

                irf = float(spot_wise_irfs[index_of_max])
                failure_results.append(
                    FailureResult(
                        FailureModeEnum(int(spot_wise_modes[index_of_max])).name,
                        irf,
                        _irf2rf(irf),
                        _irf2mos(irf),
                    )
                )

    return failure_results


def get_through_the_thickness_results(
    solid_stack: SolidStack,
    element_info_provider: ElementInfoProvider,
    result_field: dpf.Field,
    component_names: list[str],
) -> dict[str, Sequence[float]]:
    """
    Get through-the-thickness results of the solid stack.

    The results, for instance s1, s2, ..., and s23, are extracted at to bottom and top of
    each ply for each element in the stack. So, the result field must have location element_nodal
    and data at the bottom and top of each layer (ply).

    The component names are to be provided as a list of strings, for instance ['s11', 's22', 's33']
    and in the correct order so that the first entry (e.g. s11) is the first entry in the result vector.

    Example:
        results = get_through_the_thickness_results(solid_stack, element_info_provider, stress_field, ["s11", "s22"])
    """

    results = {k: [] for k in component_names}

    for element_index, element_id in enumerate(solid_stack.element_ids):
        element_info = element_info_provider.get_element_info(element_id)
        this_element_values = result_field.get_entity_data_by_id(element_id)

        plies = solid_stack.element_wise_analysis_plies[element_id]
        for ply_index, ply_id in enumerate(plies):
            for spot in SOLID_SPOTS:
                # select all data points of the ply / layers (all nodes and spots)
                selected_indices = get_selected_indices(
                    element_info, layers=[ply_index], nodes=None, spots=[spot]
                )
                for component_index, component_name in enumerate(component_names):
                    ave_value = np.average(this_element_values[selected_indices][:, component_index])
                    results[component_name].append(float(ave_value))

    return results
