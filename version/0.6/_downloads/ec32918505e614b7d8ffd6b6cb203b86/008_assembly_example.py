# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
from ansys.dpf.composites.server_helpers import (
    connect_to_or_start_server,
    version_equal_or_later,
    version_older_than,
)

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
# Plot the maximum IRF per (solid) element.
output_all_elements = composite_model.evaluate_failure_criteria(combined_criterion=combined_fc)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Plot IRF on the reference surface
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot the maximum IRF on the reference surface
if version_equal_or_later(server, "8.0"):
    irf_field = output_all_elements.get_field(
        {"failure_label": FailureOutput.FAILURE_VALUE_REF_SURFACE}
    )
    irf_field.plot()


# %%
# Get element information
# ~~~~~~~~~~~~~~~~~~~~~~~
# In the assembly, two composite definitions exist: one with a "shell" label
# and one with a "solid" label. For DPF Server versions earlier than 7.0,
# the lay-up properties must be queried with the correct composite definition label. The code
# following gets element information for all layered elements.
# For DPF Server versions 7.0 and later, element information can be retrieved directly.

if version_older_than(server, "7.0"):
    element_infos = []
    for composite_label in composite_model.composite_definition_labels:
        for (
            element_id
        ) in composite_model.get_all_layered_element_ids_for_composite_definition_label(
            composite_label
        ):
            element_infos.append(composite_model.get_element_info(element_id, composite_label))

else:
    element_infos = []
    for element_id in composite_model.get_all_layered_element_ids():
        element_infos.append(composite_model.get_element_info(element_id))
