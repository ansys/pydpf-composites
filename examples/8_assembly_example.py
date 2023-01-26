"""
.. _assembly_example:

Post-process an Assembly
------------------------

Post-process an assembly with multiple composite parts.

This example shows how an assembly of a shell and solid composite
model can be post-processed. The :class:`Composite Model <.CompositeModel>`
helps to access the data of the different parts.

"""
# %%
# Script
# ~~~~~~
#
# Load Ansys libraries

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a server and get the examples files.
# This will copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "assembly")

# %%
# Configure the combined failure criterion
combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[MaxStressCriterion()],
)

# %%
# Set up the composite model
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Plot the max IRF per element
#
output_all_elements = composite_model.evaluate_failure_criteria(combined_criterion=combined_fc)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# In the assembly exist two composite definitions, one with the label "shell" and one
# with the label "solid". To query the layup properties we have to query the
# properties with the correct ``composite_definition_label``.
# This example shows how to get ElementInfo for all layered elements
#
element_infos = []
for composite_label in composite_model.composite_definition_labels:
    for element_id in composite_model.get_all_layered_element_ids_for_composite_definition_label(
        composite_label
    ):
        element_infos.append(composite_model.get_element_info(element_id, composite_label))
