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
.. _failure_operator_example:

Composite failure analysis
--------------------------

This example shows how to analyze a composite structure by a combined failure criterion.

The failure operator of DPF Composites computes the minimum and maximum failure values
and failure modes of a combined failure criterion. A combined failure criterion is a selection of
failure criteria such as Puck, Tsai-Wu, or face sheet wrinkling. For a list of all
failure criteria, see :ref:`failure_criteria`.

The :class:`Combined Failure Criterion
<.failure_criteria.CombinedFailureCriterion>` class
allows you to assess different type of materials and failure modes at once.
The scoping enables you to evaluate the minimum and maximum failures per element
or select a list of materials or plies.

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

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Configure combined failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure the combined failure criterion.


combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
        CoreFailureCriterion(),
        VonMisesCriterion(vme=True, vms=False),
    ],
)

# %%
# Set up model and evaluate failures
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set up the composite model.

composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Evaluate failures for the entire model
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Scope failure evaluation to a certain element scope.
output_two_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
    composite_scope=CompositeScope(elements=[1, 3]),
)
irf_field = output_two_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Scope failure evaluation by plies.
output_woven_plies = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
    composite_scope=CompositeScope(plies=["P1L1__ud_patch ns1"]),
)
irf_field = output_woven_plies.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()
