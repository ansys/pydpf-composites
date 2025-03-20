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
.. _solid_model_example:

Postprocess a solid model
-------------------------

This example shows features which are tailored for the postprocessing of
solid models. These are

  - Failure plot on the reference surface
  - Sampling point for solid elements

The model is an assembly with solid and shell elements. So, the example also
demonstrates how to distinguish between different element types.

.. note::

    When using a Workbench project,
    use the :func:`.get_composite_files_from_workbench_result_folder`
    method to obtain the input files.

"""
# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading Ansys libraries, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries.

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    FaceSheetWrinklingCriterion,
    HashinCriterion,
    MaxStressCriterion,
)
from ansys.dpf.composites.layup_info import SolidStackProvider
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.solid_stack_results import get_through_the_thickness_results

# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()

composite_files_on_server = get_continuous_fiber_example_files(server, "assembly")

# %%
# Configure combined failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure the combined failure criterion.
combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[
        MaxStressCriterion(),
        CoreFailureCriterion(),
        FaceSheetWrinklingCriterion(),
        HashinCriterion(),
    ],
)


# %%
# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Plot failure results on reference surface
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The first feature is to plot the failure results on the reference surface.
# This feature projects the overall maximum failure value and according failure model
# from the solid elements to the shell elements.
# This makes the critical areas of the solid elements visible on the reference surface.
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
)

irf_on_ref_surface_field = output_all_elements.get_field(
    {"failure_label": FailureOutput.FAILURE_VALUE_REF_SURFACE}
)
irf_on_ref_surface_field.plot()

# The next plot shows the same failure analysis without the projection
# to the reference surface for the sake of comparison.
irf_max_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_max_field.plot()

# %%
# Sampling point for solids
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# The next feature is to create a sampling point for solid elements.
# The user selects one solid element and the feature automatically selects
# the entire stack of solid elements of the laminate to plot the
# through-the-thickness results. So, the first step is to find the
# critical solid element(s). In this example, the one with the highest IRF is selected.

critical_solid_id = 0
critical_irf = -1.0
critical_solid_elements = {}
for index, element_id in enumerate(irf_max_field.scoping.ids):
    # only consider solid elements because the model is an assembly of shells and solids
    if not composite_model.get_element_info(element_id).is_shell:
        irf = irf_max_field.get_entity_data(index)[0]
        if irf > critical_irf:
            critical_solid_id = element_id
            critical_irf = irf


sampling_point_solid_stack = composite_model.get_sampling_point(
    combined_criterion=combined_fc, element_id=critical_solid_id
)

# %%
# The plot shows the lay-up of the solid stack, stresses and failure results.
# The solid elements are indicated in the layup plot by the colored boxes.
# In this case, the first solid element has 3 layers, the second has 1 layer (core),
# and the third has 2 layers.
core_scale_factor = 0.2
sampling_point_plot = sampling_point_solid_stack.get_result_plots(
    strain_components=(),  # Skip strains
    core_scale_factor=core_scale_factor,
    failure_components=(FailureMeasureEnum.INVERSE_RESERVE_FACTOR,),
    show_failure_modes=True,
)
sampling_point_plot.figure.set_figheight(8)
sampling_point_plot.figure.set_figwidth(12)
sampling_point_plot.figure.show()

# %%
# Here is another sampling point plot with the in-plane strains only
# and the colored boxes to indicate the solid elements are added
# to the plot as well.
sampling_point_plot = sampling_point_solid_stack.get_result_plots(
    strain_components=("e1", "e2", "e12"),  # Show in-plane results only
    stress_components=(),  # Don't show stresses
    failure_components=(),
    core_scale_factor=core_scale_factor,
    create_laminate_plot=False,
    show_failure_modes=True,
)
sampling_point_solid_stack.add_element_boxes_to_plot(
    axes=sampling_point_plot.axes,
    core_scale_factor=core_scale_factor,
    alpha=0.15,
)
sampling_point_plot.figure.set_figheight(8)
sampling_point_plot.figure.set_figwidth(12)
sampling_point_plot.figure.show()


# %%
# Solid Stack Information
# ~~~~~~~~~~~~~~~~~~~~~~~
# Information about the stack of solid elements can be retrieved
# by using the SolidStackProvider. A basic example is shown below
# where 6 is the element ID (label) and not an index.
solid_stack_provider = SolidStackProvider(
    composite_model.get_mesh(), composite_model.get_layup_operator()
)
print(f"Number of solid stacks: {solid_stack_provider.number_of_stacks}")
stack_of_element_6 = solid_stack_provider.get_solid_stack(6)
print(f"Solid stack of element 6: {stack_of_element_6}")

# %%
# The solid stack can then be used for example to get the through-the-thickness results.
# In this example, s11, s22 and s12 are retrieved for the last time step.
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_container = stress_operator.outputs.fields_container()
stress_field = stress_container.get_field(
    {
        "time": stress_container.get_available_ids_for_label("time")[-1],
    }
)

results = get_through_the_thickness_results(
    solid_stack=stack_of_element_6,
    element_info_provider=composite_model.get_element_info_provider(),
    result_field=stress_field,
    component_names=("s11", "s22", "s12"),
)
print(results)