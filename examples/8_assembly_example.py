"""
.. _assembly_example:

CompositeModel for an Assembly Model
------------------------------------

Post-process an assembly with multiple composite parts.

This example shows how an assembly of a shell and solid composite
model can be post-processed. The :class:`Composite Model <ansys.dpf.composites.CompositeModel>`
helps to operator on the individual parts and to access all the data.

"""
# %%
# Load ansys libraries

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.enums import FailureOutput
from ansys.dpf.composites.example_helper.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion

server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "assembly")


# %%
# Definition of the combined failure criterion
def get_combined_failure_criterion() -> CombinedFailureCriterion:
    return CombinedFailureCriterion(
        name="failure of all materials",
        failure_criteria=[MaxStressCriterion()],
    )


# %%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server)
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion()
)

# %%
# Plot the max IRF per element
#

irf_field = output_all_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()


# %%
# In the assembly exist two composite definition, one with the label "shell" and one
# with the label "solid". To query the layup properties we have to query the
# properties with the correct composite_definition_label.
# This example shows how to get ElementInfo for all layered elements
#
element_infos = []
for composite_label in composite_model.composite_definition_labels:
    for element_id in composite_model.get_all_layered_element_ids_for_composite_definition_label(
        composite_label
    ):
        element_infos.append(composite_model.get_element_info(element_id, composite_label))
