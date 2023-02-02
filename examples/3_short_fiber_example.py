"""
.. _short_fiber_example:

Failure analysis for short fiber composites
-------------------------------------------

Ansys 2021 R2 introduced a beta feature for short fiber workflows.
This example shows how you can use this beta feature to evaluate failures
of a short fiber reinforced part. It configures the DPF operator
``short_fiber_failure_criterion_evaluator`` to compute Tsai-Hill type
orientation tensor-dependent failure criteria and then generates plots.

The model shown in this example consists of a tensile specimen made of
a short glass fiber reinforced thermoplastic injection molded from both sides.
"""
# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading Ansys libraries, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries.
import ansys.dpf.core as dpf

from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_short_fiber_example_files
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
# These files are needed:
#
# * Mechanical APDL result (RST) file containing the simulation results
# * Engineering Data (MATML) file containing the material properties of the composite
# * Mechanical APDL input file (DS.DAT) containing the fiber orientation tensor data
server = connect_to_or_start_server()
composite_files_on_server = get_short_fiber_example_files(server, "short_fiber")

# %%
# Set up data sources
# ~~~~~~~~~~~~~~~~~~~
# Set up the data sources.
data_sources = dpf.DataSources()
data_sources.add_file_path(composite_files_on_server.engineering_data, "EngineeringData")
data_sources.add_file_path(composite_files_on_server.dsdat, "dat")
data_sources.set_result_file_path(composite_files_on_server.rst)

# %%
# Initialize DPF model
# ~~~~~~~~~~~~~~~~~~~~
# Initialize the DPF model.
model = dpf.Model(composite_files_on_server.rst)
mesh = model.metadata.meshed_region

# %%
# Plot results
# ~~~~~~~~~~~~
# Plot the two largest eigenvalues (a11 and a22) of the fiber orientation tensor.
# Note that the plots reveal the presence of a weld line in the middle of the specimen.
field_variable_provider = dpf.Operator("composite::inistate_field_variables_provider")
field_variable_provider.inputs.data_sources(data_sources)
field_variable_provider.inputs.mesh(model.metadata.mesh_provider)

field_variables = field_variable_provider.outputs.fields_container.get_data()

a11 = field_variables[0]
a11.plot()

a22 = field_variables[1]
a22.plot()

# %%
# Configure and evaluate
# ~~~~~~~~~~~~~~~~~~~~~~
# Configure the short fiber failure criterion evaluator and evaluate.
# Note that you can specify optional time and mesh scoping inputs.
sf_op = dpf.Operator("composite::short_fiber_failure_criterion_evaluator")
sf_op.inputs.streams_container(model.metadata.streams_provider)
sf_op.inputs.data_sources(data_sources)
sf_op.inputs.stress_limit_type("ultimate")  # "yield" or "ultimate" (default)
sf_op.run()

# %%
# Compute and plot results
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compute and plot the maximum failure value per element.
mat_support_operator = dpf.Operator("mat_support_provider")
mat_support_operator.connect(4, data_sources)

minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.inputs.fields_container(sf_op)
minmax_per_element.inputs.mesh(mesh)
minmax_per_element.inputs.abstract_field_support(mat_support_operator)

max_failure = minmax_per_element.outputs.field_max.get_data()
max_failure_value = max_failure.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
mesh.plot(max_failure_value, show_edges=True)
