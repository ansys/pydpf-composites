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
"""Functions to retrieve through-the-thickness results of a stack of solid elements."""
from collections.abc import Sequence

import ansys.dpf.core as dpf
import numpy as np

from .constants import Spot, component_index_from_name
from .failure_criteria import FailureModeEnum
from .layup_info import ElementInfo, ElementInfoProviderProtocol, SolidStack
from .sampling_point_types import FailureResult
from .select_indices import get_selected_indices

__all__ = (
    "get_through_the_thickness_failure_results",
    "get_through_the_thickness_results",
)

MAX_RESERVE_FACTOR = 1000.0
SOLID_SPOTS = [Spot.BOTTOM, Spot.TOP]


def _irf2rf(irf: float) -> float:
    if irf == 0.0:
        return MAX_RESERVE_FACTOR

    rf = 1.0 / irf
    return min(rf, MAX_RESERVE_FACTOR)


def _irf2mos(irf: float) -> float:
    rf = _irf2rf(irf)
    return rf - 1.0


def _get_element_info(
    element_info_provider: ElementInfoProviderProtocol, element_id: int
) -> ElementInfo:
    e_info = element_info_provider.get_element_info(element_id)
    if not e_info:
        raise RuntimeError(f"Could not retrieve element info for {element_id}")
    return e_info


def get_through_the_thickness_failure_results(
    solid_stack: SolidStack,
    element_info_provider: ElementInfoProviderProtocol,
    irf_field: dpf.Field,
    failure_mode_field: dpf.Field,
) -> list[FailureResult]:
    """Get through-the-thickness failure results of the solid stack.

    The maximum IRF is extracted at the bottom and top of each ply for each element in
    the stack. The result contains the failure mode, IRF, reserve factor and margin of
    safety for each spot and ply. The inputs irf_field and failure_mode_field are
    expected to have location element_nodal (no data reduction) with data at the
    bottom and top of each layer (ply).

    In case of drop-off or cut-off elements, which are non-layered, the maximum IRF is extracted.

    Example
    -------
    >>> failures = get_through_the_thickness_failure_results(
    ...     stack, element_info_provider, irf_field, failure_mode_field
    ... )
    """
    failure_results = []

    for _, level_element_ids in solid_stack.element_ids_per_level.items():
        is_layered = False
        if len(level_element_ids) == 1:
            element_id = level_element_ids[0]
            element_info = _get_element_info(element_info_provider, element_id)
            is_layered = element_info.is_layered
            if is_layered:
                this_element_irfs = irf_field.get_entity_data_by_id(element_id)
                this_element_modes = failure_mode_field.get_entity_data_by_id(element_id)

                for ply_index, _ in enumerate(solid_stack.element_wise_analysis_plies[element_id]):
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

        if not is_layered:
            num_plies = len(solid_stack.element_wise_analysis_plies[level_element_ids[0]])
            for element_id in level_element_ids:
                if num_plies != len(solid_stack.element_wise_analysis_plies[element_id]):
                    raise RuntimeError("Number of plies mismatch!")

            max_irf = -1.0
            max_failure_mode = None
            for element_id in level_element_ids:
                this_element_irfs = irf_field.get_entity_data_by_id(element_id)
                this_element_modes = failure_mode_field.get_entity_data_by_id(element_id)

                # homogeneous element: there is no spot and so the same value is stored
                # for both spots
                index_of_max = this_element_irfs.argmax()
                irf = float(this_element_irfs[index_of_max])
                if irf > max_irf:
                    max_irf = irf
                    max_failure_mode = int(this_element_modes[index_of_max])

            f_res = FailureResult(
                FailureModeEnum(max_failure_mode).name,
                max_irf,
                _irf2rf(max_irf),
                _irf2mos(max_irf),
            )

            failure_results.extend(num_plies * len(SOLID_SPOTS) * [f_res])

    return failure_results


def get_through_the_thickness_results(
    solid_stack: SolidStack,
    element_info_provider: ElementInfoProviderProtocol,
    result_field: dpf.Field,
    component_names: Sequence[str],
) -> dict[str, list[float]]:
    """Get through-the-thickness results of the solid stack.

    The results, for instance s1, s2, ..., and s23, are extracted at to bottom and top of
    each ply for each element in the stack. So, the result field must be available at the
    location ``element_nodal`` and data at the bottom and top of each layer (ply).
    Finally, the average value per spot is stored in the result vector.

    The component names are to be provided as a tuple of strings, for instance
    ('s11', 's22', 's33').

    In case of drop-off or cut-off elements, which are non-layered, the average result is used.

    Example
    -------
    >>> results = get_through_the_thickness_results(
    ...      solid_stack, element_info_provider, stress_field, ("s1", "s2")
    ... )
    """
    results: dict[str, list[float]] = {k: [] for k in component_names}

    for _, level_element_ids in solid_stack.element_ids_per_level.items():
        is_layered = False
        if len(level_element_ids) == 1:
            element_id = level_element_ids[0]
            element_info = _get_element_info(element_info_provider, element_id)
            is_layered = element_info.is_layered
            if is_layered:
                this_element_values = result_field.get_entity_data_by_id(element_id)
                for ply_index in range(0, len(solid_stack.element_wise_analysis_plies[element_id])):
                    for spot in SOLID_SPOTS:
                        # select all data points of the ply / layers (all nodes and spots)
                        selected_indices = get_selected_indices(
                            element_info, layers=[int(ply_index)], nodes=None, spots=[spot]
                        )
                        for comp_name in component_names:
                            component_index = component_index_from_name(comp_name)
                            ave_value = np.average(
                                this_element_values[selected_indices][:, component_index]
                            )
                            results[comp_name].append(float(ave_value))

        if not is_layered:
            # Multiple homogeneous elements. The results are averaged over all elements
            # Assumption: all elements origin from the same layered element, and so
            # they have the same "artificial" plies.
            # The ply information is needed to sync the lay-up plot with the results plot.
            homogeneous_results: dict[str, list[float]] = {k: [] for k in component_names}
            num_plies = len(solid_stack.element_wise_analysis_plies[level_element_ids[0]])
            for element_id in level_element_ids:
                if num_plies != len(solid_stack.element_wise_analysis_plies[element_id]):
                    raise RuntimeError("Number of plies mismatch!")

            for element_id in level_element_ids:
                this_element_values = result_field.get_entity_data_by_id(element_id)

                # homogeneous element: there is no spot and so the same value is
                # stored for both spots
                for comp_name in component_names:
                    component_index = component_index_from_name(comp_name)
                    ave_value = np.average(this_element_values[:, component_index])
                    homogeneous_results[comp_name].append(float(ave_value))

            # average the element-wise results since this level consist of
            # multiple homogeneous elements
            for comp_name in component_names:
                ave_value = np.average(homogeneous_results[comp_name])
                results[comp_name].extend(num_plies * len(SOLID_SPOTS) * [float(ave_value)])

    return results
