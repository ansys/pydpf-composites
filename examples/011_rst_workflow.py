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
.. _rst_workflow_example:

Failure analysis of an MAPDL (RST) model
----------------------------------------

This example shows the postprocessing of an MAPDL (RST) model with layered elements that was not
preprocessed by ACP. The difference between the RST-only and ACP-based workflow is that
the section data are loaded from the RST file instead of the ACP layup file.
This happens automatically if the parameter `composite` of the
:class:`.ContinuousFiberCompositesFiles` class is not set.

The engineering data file (XML or ENGD) with the material properties is needed anyway.
Otherwise, the material properties cannot be mapped.
At the end of this example, two workflows are shown on how to create
the engineering data file based on a MAPDL model and how to set the
material UUIDs in MAPDL.

.. important::
   The material UUIDs in the engineering data file must be identical
   to the UUIDs in Mechanical APDL (RST file). A detailed explanation
   can be found at the end of this example.

The postprocessing of MAPDL models is supported in 2024 R2 (DPF Server version 8.0)
and later. A few advanced features are not supported with the RST only workflow.
For more information, see :ref:`limitations`.

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

import ansys.dpf.core as dpf

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    FaceSheetWrinklingCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()

# %%
# Get input files (RST and material.engd but skip the ACP layup file).
composite_files_on_server = get_continuous_fiber_example_files(server, "shell", True)
print(composite_files_on_server)

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
        FaceSheetWrinklingCriterion(),
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
# Create and plot a sampling point
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
sampling_point = composite_model.get_sampling_point(combined_criterion=combined_fc, element_id=2)
sampling_plot = sampling_point.get_result_plots(core_scale_factor=0.1)
sampling_plot.figure.show()

# %% Layer-wise failure criteria
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The next lines show how to compute layer-wise failure criteria
# and how to access the data of each layer.

# %%
# Create a combined failure criterion
combined_fc = CombinedFailureCriterion(
    name="My Failure Criteria",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
    ],
)

# %%
# Prepare and configure inputs for the multiple failure criteria operator
# Note: the output has the same format as the input
# (strain and stress fields). So there is one failure value and mode for each
# integration point, layer and element, for all time steps.
strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.inputs.configuration(combined_fc.to_json())
failure_evaluator.inputs.materials_container(
    composite_model.material_operators.material_provider.outputs
)
failure_evaluator.inputs.strains_container(strain_operator.outputs.fields_container)
failure_evaluator.inputs.stresses_container(stress_operator.outputs.fields_container)
failure_evaluator.inputs.mesh(composite_model.get_mesh())
irf_field = failure_evaluator.outputs.fields_container.get_data().get_field(
    {"failure_label": FailureOutput.FAILURE_VALUE, "time": 1}
)
failure_mode_field = failure_evaluator.outputs.fields_container.get_data().get_field(
    {"failure_label": FailureOutput.FAILURE_MODE, "time": 1}
)

# %%
# Access the data of each layer. Details about how to store custom
# data in a DPF field is shown at the end of
# :ref:`sphx_glr_examples_gallery_examples_004_get_material_properties_example.py`.

for element_id in irf_field.scoping.ids:
    irf_data = irf_field.get_entity_data_by_id(element_id)
    model_data = failure_mode_field.get_entity_data_by_id(element_id)
    element_info = composite_model.get_element_info(element_id)
    element_max = 0
    for layer_index, dpf_material_id in enumerate(element_info.dpf_material_ids):
        selected_indices = get_selected_indices(element_info, layers=[layer_index])
        layer_irf_values = irf_data[selected_indices]
        layer_mode_values = model_data[selected_indices]
        # Do something with the layer data

# %%
# Create Engineering Data file and set material UUIDs in MAPDL
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Here are two workflows for setting up the engineering data file
# and the material UUIDs in MAPDL. The material UUIDs must be set
# in MAPDL before the model is solved.
#
# With WB and Engineering Data:
#   - Create an External Model system in WB and load the solver input file
#   - Link the External Model with an Engineering Data system and update it
#   - Save the project and copy the generated engineering data file (EngineeringData.xml)
#   - For each material, look for the ``DataTransferID``, go to MAPDL and set the material
#     UUIDs with the ``MP,UVID,<material index>,<value>`` command
#
# With ACP Standalone (for constant material properties only):
#   - Start ACP, go to *File - Import Model* and load the solver input file (CDB)
#   - Go to the Materials folder and export the engineering data file (Ansys Workbench XML)
#   - For each material, look for the ``DataTransferID``, go to MAPDL and set the material
#     UUID with the ``MP,UVID,<material index>,<value>`` command.
