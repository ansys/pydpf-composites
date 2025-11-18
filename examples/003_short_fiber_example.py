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
.. _short_fiber_example:

Failure analysis for short fiber composites
-------------------------------------------

This example shows how to evaluate failures of a short fiber reinforced
part.

As part of the short fiber workflows, you can evaluate and plot Tsai-Hill
type orientation tensor-dependent failure criteria. This example shows
how to configure the DPF operator ``short_fiber_failure_criterion_evaluator``
to compute such failure criteria.

The model shown in this example consists of a tensile specimen made of
a short glass fiber reinforced thermoplastic injection molded from both sides.

.. note::

    The evaluation of failure criteria in short fiber workflows is a
    beta feature, introduced in Ansys 2021 R2.

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
from ansys.dpf.composites.data_sources import get_short_fiber_composites_data_sources
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
data_sources = get_short_fiber_composites_data_sources(composite_files_on_server)

# %%
# Initialize DPF model
# ~~~~~~~~~~~~~~~~~~~~
# Initialize the DPF model.
model = dpf.Model(data_sources=data_sources)
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

# %%
# The order of field variables is not deterministic. For consistent output,
# they are sorted by name.
for field_variable in sorted(field_variables, key=lambda fv: fv.name):
    print(f"Field variable: {field_variable.name}")
    field_variable.plot()

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
minmax_per_element.inputs.material_support(mat_support_operator)

max_failure = minmax_per_element.outputs.field_max.get_data()
max_failure_value = max_failure.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
mesh.plot(max_failure_value, show_edges=True)
