"""
.. _assembly_example:

Postprocess an assembly
-----------------------

This example shows how to postprocess an assembly with multiple composite parts.
The assembly consists of a shell and solid composite model. The
:class:`Composite Model <.CompositeModel>` class is used to access
the data of the different parts.

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
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "assembly")

# %%
# Configure combined failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure the combined failure crition.
combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[MaxStressCriterion()],
)

# %%
# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Plot IRF
# ~~~~~~~~
# Plot the maximum IRF per element.
output_all_elements = composite_model.evaluate_failure_criteria(combined_criterion=combined_fc)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Get element information
# ~~~~~~~~~~~~~~~~~~~~~~~
# In the assembly, two composite definitions exist: one with a "shell" label
# and one with a "solid" label. To query the lay-up properties, you must query the
# properties with the correct composite definition label. This code
# gets element information for all layered elements.
#
element_infos = []
for composite_label in composite_model.composite_definition_labels:
    for element_id in composite_model.get_all_layered_element_ids_for_composite_definition_label(
        composite_label
    ):
        element_infos.append(composite_model.get_element_info(element_id, composite_label))