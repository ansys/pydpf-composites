"""
.. _short_fiber_example:

Short Fiber Failure Analysis
----------------------------

Failure analysis for a short fiber-reinforced part.

This example shows how to configure the DPF operator
*short_fiber_failure_criterion_evaluator* which enables the failure evaluation
of short fiber composites.

"""
# %%
# Script
# ~~~~~~
#
# Load Ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.example_helper.example_helper import get_short_fiber_example_files

# %%
# Start a server and get the examples files.
# This will copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_short_fiber_example_files(server, "short_fiber")


# %%
# Set up data sources
data_sources = dpf.DataSources()
data_sources.add_file_path(composite_files_on_server.engineering_data, "EngineeringData")
data_sources.add_file_path(composite_files_on_server.dsdat, "dat")
data_sources.set_result_file_path(composite_files_on_server.rst)

# %%
# Initialize DPF model
model = dpf.Model(composite_files_on_server.rst)

# %%
# Configure the Short Fiber Failure Criterion Evaluator
sf_op = dpf.Operator("composite::short_fiber_failure_criterion_evaluator")
sf_op.inputs.data_sources(data_sources)
sf_op.inputs.stress_limit_type("ultimate")  # "yield" or "ultimate" (default)
sf_op.run()

mat_support_operator = dpf.Operator("mat_support_provider")
mat_support_operator.connect(4, data_sources)

minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.inputs.fields_container(sf_op)
minmax_per_element.inputs.mesh(model.metadata.meshed_region)
minmax_per_element.inputs.abstract_field_support(mat_support_operator)
max_element_stress_cont = minmax_per_element.get_output(1, dpf.types.fields_container)
fc_mode = max_element_stress_cont[0]
fc_value = max_element_stress_cont[1]
mesh = model.metadata.meshed_region
mesh.plot(fc_value, show_edges=True)