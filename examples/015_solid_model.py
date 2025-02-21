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

"""
.. _assembly_example:

Postprocess an assembly
-----------------------

This example shows how to postprocess an assembly with multiple composite parts.
The assembly consists of a shell and solid composite model. The
:class:`Composite Model <.CompositeModel>` class is used to access
the data of the different parts.

.. note::

    When using a Workbench project,
    use the :func:`.composite_files_from_workbench_harmonic_analysis`
    method to obtain the input files.

"""
# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading Ansys libraries, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries.

from dataclasses import dataclass
from typing import Dict, List

import ansys.dpf.core as dpf
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from ansys.dpf.composites.composite_model import CompositeModel, LayerProperty
from ansys.dpf.composites.constants import FailureOutput, Sym3x3TensorComponent
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    FailureModeEnum,
    MaxStressCriterion,
)
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()

result_folder = r"D:\tmp\ge_blade_files\dp0\SYS\MECH"
composite_files = get_composite_files_from_workbench_result_folder(result_folder)

# Configure combined failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure the combined failure criterion.
combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[MaxStressCriterion()],
)

# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files, server)

# %%
# Solid Stack Information
# ~~~~~~~~~~~~~~~~~~~~~~~
# In the assembly, two composite definitions exist: one with a "shell" label
# and one with a "solid" label. For DPF Server versions earlier than 7.0,
# the lay-up properties must be queried with the correct composite definition label. The code
# following gets element information for all layered elements.
# For DPF Server versions 7.0 and later, element information can be retrieved directly.

solid_stacks_property_field = composite_model.get_mesh().property_field("solid_stacks")


@dataclass(frozen=True)
class SolidStack:
    # list of element labels
    element_ids: list[int]
    element_wise_analysis_plies: dict[int, list[str]]
    # z-coordinates bottom, mid and top for each ply
    offsets: list[list[float]]

    def get_through_the_thickness_failure_results(
        self,
        composite_model: CompositeModel,
        irf_field: dpf.Field,
        failure_mode_field: dpf.Field | None,
    ) -> tuple[NDArray, NDArray | None, NDArray]:
        """
        Get through-the-thickness failure results for the solid stack.

        The maximum IRF is extracted for each ply in the stack, the corresponding offset at the middle of the ply,
        and if available, the corresponding failure mode.
        Note: the field must have ply-wise data.

        Example:
            irfs_of_stack, modes_of_stack, offsets = stack.get_through_the_thickness_failure_results(composite_model, irf_field, failure_mode_field)
        """
        through_the_thickness_irfs = []
        through_the_thickness_modes = []
        ttt_offsets = []

        stack_ply_index = 0
        for element_index, element_id in enumerate(self.element_ids):
            element_info = composite_model.get_element_info(element_id)
            this_element_irfs = irf_field.get_entity_data_by_id(element_id)
            if failure_mode_field:
                this_element_modes = failure_model_field.get_entity_data_by_id(element_id)

            plies = self.element_wise_analysis_plies[element_id]
            for ply_index, ply_id in enumerate(plies):
                # select all data points of the ply / layers (all nodes and spots)
                selected_indices = get_selected_indices(
                    element_info, layers=[ply_index], nodes=None, spots=None
                )
                ply_wise_irfs = this_element_irfs[selected_indices]
                index_of_max = ply_wise_irfs.argmax()
                through_the_thickness_irfs.append(ply_wise_irfs[index_of_max])

                if failure_mode_field:
                    ply_wise_modes = this_element_modes[selected_indices]
                    through_the_thickness_modes.append(ply_wise_modes[index_of_max])

                ttt_offsets.append(self.offsets[stack_ply_index][1])  # mid thickness
                stack_ply_index += 1

        if failure_mode_field:
            return (
                np.array(through_the_thickness_irfs),
                np.array(through_the_thickness_modes),
                np.array(ttt_offsets),
            )
        else:
            return np.array(through_the_thickness_irfs), None, np.array(ttt_offsets)

    def get_through_the_thickness_results(
        self,
        composite_model: CompositeModel,
        result_field: dpf.Field,
        component: Sym3x3TensorComponent,
    ) -> tuple[NDArray, NDArray]:
        """
        Get through-the-thickness results for the solid stack.

        The maximum of the selected component is extracted, the corresponding offset at the middle of the ply,
        and if available, the corresponding failure mode.
        Note: the field must have plz-wise data.

        Example:
            stresses, offsets = stack.get_through_the_thickness_results(composite_model, stress_field, Sym3x3TensorComponent.TENSOR11)
        """
        through_the_thickness_res = []
        ttt_offsets = []

        stack_ply_index = 0
        for element_index, element_id in enumerate(self.element_ids):
            element_info = composite_model.get_element_info(element_id)
            this_element_results = result_field.get_entity_data_by_id(element_id)

            plies = self.element_wise_analysis_plies[element_id]
            for ply_index, ply_id in enumerate(plies):
                # select all data points of the ply / layers (all nodes and spots)
                selected_indices = get_selected_indices(
                    element_info, layers=[ply_index], nodes=None, spots=None
                )
                ply_wise_res = this_element_results[selected_indices][:, component]
                through_the_thickness_res.append(ply_wise_res.max())
                ttt_offsets.append(self.offsets[stack_ply_index][1])  # mid thickness
                stack_ply_index += 1

        return np.array(through_the_thickness_res), np.array(ttt_offsets)


class SolidStackProvider:

    SOLID_STACK_PROPERTY_FIELD_NAME = "solid_stacks"

    def __init__(self, model: CompositeModel):
        self._composite_model = model
        self._mesh = model.get_mesh()
        if self.SOLID_STACK_PROPERTY_FIELD_NAME not in self._mesh.available_property_fields:
            raise RuntimeError(
                f"Property field '{self.SOLID_STACK_PROPERTY_FIELD_NAME}' not found in mesh."
            )

        self._solid_stacks_property_field = self._mesh.property_field(
            self.SOLID_STACK_PROPERTY_FIELD_NAME
        )

        self._element_id_to_solid_stack_index_map = {}
        self.solid_stacks: list[SolidStack] = []
        # prepare solid stack info
        self._prepare_data()

    def num_stacks(self):
        return self._solid_stacks_property_field.scoping.size

    def _prepare_data(self):
        print(f"Number of solid stacks: {self.num_stacks()}")
        for index in range(0, self.num_stacks()):
            elementary_data = self._solid_stacks_property_field.get_entity_data(index)
            element_ids = []
            element_wise_analysis_plies = {}
            coords = []
            current_offset = 0.0
            for element_id, level in elementary_data:
                ply_ids = self._composite_model.get_analysis_plies(element_id)
                if ply_ids:
                    # only proces elements with plies
                    element_ids.append(int(element_id))
                    ply_ids = self._composite_model.get_analysis_plies(element_id)
                    thicknesses = self._composite_model.get_property_for_all_layers(
                        LayerProperty.THICKNESSES, element_id
                    )
                    element_wise_analysis_plies[element_id] = ply_ids
                    for ply_index, ply_id in enumerate(ply_ids):
                        th = thicknesses[ply_index]
                        coords.append(
                            [current_offset, current_offset + th / 2.0, current_offset + th]
                        )
                        current_offset += th
                    self._element_id_to_solid_stack_index_map[element_id] = len(self.solid_stacks)

            self.solid_stacks.append(
                SolidStack(
                    element_ids=element_ids,
                    element_wise_analysis_plies=element_wise_analysis_plies,
                    offsets=coords,
                )
            )

    def get_solid_stack(self, element_id: int) -> SolidStack | None:
        """Get the full solid stack for a given element.

        Returns None if the element is not part of a solid stack.
        """
        if element_id in self._element_id_to_solid_stack_index_map:
            solid_stack_index = self._element_id_to_solid_stack_index_map[element_id]
            return self.solid_stacks[solid_stack_index]
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


# Compute failure criteria and modes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Evaluates the failure criteria for each element, ply and integration point
# and the corresponding failure mode.
stresses_op = composite_model.core_model.results.stress()
stresses_op.inputs.bool_rotate_to_global(False)

elastic_strain_op = composite_model.core_model.results.elastic_strain()
elastic_strain_op.inputs.bool_rotate_to_global(False)

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.inputs.configuration(combined_fc.to_json())
failure_evaluator.inputs.materials_container(composite_model.material_operators.material_provider)
failure_evaluator.inputs.stresses_container(stresses_op)
failure_evaluator.inputs.strains_container(elastic_strain_op)
failure_evaluator.inputs.mesh(composite_model.get_mesh())


# Extract the most critical failure value (max irf) and corresponding mode for each element
minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.inputs.fields_container(failure_evaluator.outputs.fields_container)
minmax_per_element.inputs.mesh(composite_model.get_mesh())
minmax_per_element.inputs.material_support(
    composite_model.material_operators.material_support_provider.outputs.abstract_field_support
)

irfs_max_container = minmax_per_element.outputs.field_max()
# get result of the last time step
irf_max_field = irfs_max_container.get_field(
    {
        "failure_label": FailureOutput.FAILURE_VALUE,
        "time": irfs_max_container.get_time_scoping().ids[-1],
    }
)

irf_max_field.plot()

# Extract critical solid elements
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Find the critical solid elements with IRF > LIMIT
# and the corresponding solid stack

LIMIT = 1.0
critical_solid_elements = {}
for index, element_id in enumerate(irf_max_field.scoping.ids):
    max_irf = max(irf_max_field.get_entity_data(index))
    if max_irf > LIMIT and not composite_model.get_element_info(element_id).is_shell:
        critical_solid_elements[element_id] = max_irf

print("num critical solid elements:", len(critical_solid_elements))
PROCESS_NUM_CRITICAL_ELEMENTS = (
    20 if len(critical_solid_elements) > 20 else len(critical_solid_elements)
)
print("NUM_CRITICAL_ELEMENTS:", PROCESS_NUM_CRITICAL_ELEMENTS)
# Get the NUM_CRITICAL_ELEMENTS most critical solid elements
critical_solid_element_ids = dict(
    sorted(critical_solid_elements.items(), key=lambda x: x[1], reverse=True)[
        :PROCESS_NUM_CRITICAL_ELEMENTS
    ]
)

# Plot the through-the-thickness results
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Get the failure and stress fields
# and plot the results for the critical solid stacks

# get elemental-nodal irf field without data reduction
elemental_nodal_failure_container = failure_evaluator.outputs.fields_container.get_data()
irf_field = elemental_nodal_failure_container.get_field(
    {
        "failure_label": FailureOutput.FAILURE_VALUE,
        "time": elemental_nodal_failure_container.get_time_scoping().ids[-1],
    }
)
failure_model_field = elemental_nodal_failure_container.get_field(
    {
        "failure_label": FailureOutput.FAILURE_MODE,
        "time": elemental_nodal_failure_container.get_time_scoping().ids[-1],
    }
)
stress_field = (
    stresses_op
    .outputs.fields_container()
    .get_field(
        {
            "time": elemental_nodal_failure_container.get_time_scoping().ids[-1],
        }
    )
)

solid_stack_provider = SolidStackProvider(composite_model)
critical_solid_stacks = solid_stack_provider.get_solid_stacks(critical_solid_element_ids.keys())

print(f"Number of critical solid stacks: {len(critical_solid_stacks)}")

for stack in critical_solid_stacks:
    print(f"    Solid stacks: {stack}")
    ttt_irfs, ttt_modes, offsets = stack.get_through_the_thickness_failure_results(
        composite_model, irf_field, failure_model_field
    )
    ttt_s11, _ = stack.get_through_the_thickness_results(
        composite_model, stress_field, Sym3x3TensorComponent.TENSOR11
    )
    # print(ttt_irfs, ttt_modes, ttt_s11, offsets)
    fix, (ax1, ax2) = plt.subplots(1, 2)
    ax1.plot(ttt_irfs, offsets)
    ax1.set_title("Ply-wise IRFs")
    ax1.set_xlabel("IRF [-]")
    ax1.set_ylabel("z-Coordinate [mm]")
    index = 0
    for irf, offset in zip(ttt_irfs, offsets):
        ax1.text(x=irf, y=offset, s=FailureModeEnum(int(ttt_modes[index])).name)
        index += 1

    ax2.yaxis.tick_right()
    ax2.plot(ttt_s11, offsets)
    ax2.set_title("Ply-wise Stresses")
    ax2.set_xlabel("S11 [MPa]")
    ax2.set_yticks(offsets)
    element_plies = [
        f"{e_id}: {ply}"
        for e_id, e_plies in stack.element_wise_analysis_plies.items()
        for ply in e_plies
    ]
    ax2.set_yticklabels(element_plies)

    plt.show()
