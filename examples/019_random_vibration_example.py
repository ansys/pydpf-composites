# Copyright (C) 2022 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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
.. _random_vibration_example:

Random vibration analysis
-------------------------

This example demonstrates a failure analysis for a random vibration analysis using the Max
Stress criterion. The example calculates failure factors for both one-sigma and three-sigma values.

The directional results from a Power Spectral Density (PSD) analysis are statistical quantities.
Consequently, directional components such as X, Y, and Z displacements, strains, and stresses
cannot be combined using the standard vector or tensor operations that are applicable to 
deterministic results. As a result, failure criteria that combine multiple stress or strain
components, such as Puck and Hashin, are not applicable to PSD results.

For the same reason, stress and strain tensors should not be rotated because tensor 
rotation requires combining component values. PSD results are reported in the layer (material)
coordinate system, so no additional coordinate transformation is required.

The Maximum Stress and Maximum Strain criteria remain applicable because they evaluate each
stress or strain component independently.

The Mechanical application reports PSD-derived stress and strain results as positive one-sigma 
values. However, the actual response may occur in either the positive or negative direction, 
and orthotropic materials typically have different tensile and compressive strengths.
Therefore, evaluate the failure factors using both the positive and negative scaled results.

You can obtain failure factors for two-sigma and three-sigma values by scaling the one-sigma 
results.

.. note::

    A one-sigma value indicates that the response is expected to be below that value with a 
    probability of 68.3%. Similarly, the response is expected to be below the two-sigma
    and three-sigma values with probabilities of 95.45% and 99.73%, respectively.

"""

# %%
# Required input files
# ~~~~~~~~~~~~~~~~~~~~
# When running this workflow from the Ansys Workbench application, you must manually
# identify the required input files because the random vibration analysis is a nested
# analysis.
#
# * The result file (``.rst``) and material file (MatML.xml) are located in the solver files
#   directory of the random vibration analysis.
#
# * The composite definitions file (``ACPCompositeDefinitions.h5``) is located in the first
#   Mechanical analysis system of the workflow (for example,
#   ``..\\..\\SYS-2\\MECH\\Setup\\ACPCompositeDefinitions.h5``).
#
# * For assemblies that contain multiple Mechanical models, also provide the mapping files
#   (``.mapping``). These files are located in the same directory as the
#   ``ACPCompositeDefinitions.h5`` file.

# %%
# Set up the analysis
# ~~~~~~~~~~~~~~~~~~~~
# To set up the analysis, load the required modules, connect to the DPF server, and
# retrieve the example files.
import ansys.dpf.core as dpf

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Launch the DPF server and obtain the input files
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Start a DPF server and copy the example files to the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "random_vibration")

# Create a composite model.
composite_model = CompositeModel(composite_files_on_server, server)


# %%
# Evaluate failure
# ~~~~~~~~~~~~~~~~
# Evaluate failure for the scaled stress and strain results. This example uses a
# custom workflow to compute failure criteria for the one-sigma and three-sigma
# values. The ``multiple_failure_criteria_operator`` evaluates all failure criteria,
# and the ``minmax_per_element_operator`` extracts the minimum and maximum values
# across all failure criteria, layers, and integration points.
def run_custom_failure_evaluation(
    failure_criterion_: CombinedFailureCriterion,
    composite_model_: CompositeModel,
    stain_fields_container_: dpf.FieldsContainer,
    stress_fields_container_: dpf.FieldsContainer,
):

    failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
    failure_evaluator.inputs.configuration(failure_criterion_.to_json())
    failure_evaluator.inputs.materials_container(
        composite_model_.material_operators.material_provider.outputs
    )
    failure_evaluator.inputs.strains_container(stain_fields_container_)
    failure_evaluator.inputs.stresses_container(stress_fields_container_)
    failure_evaluator.inputs.mesh(composite_model_.get_mesh())

    minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
    minmax_per_element.inputs.fields_container(failure_evaluator.outputs.fields_container)
    minmax_per_element.inputs.mesh(composite_model_.get_mesh())
    minmax_per_element.inputs.material_support(
        composite_model_.material_operators.material_support_provider.outputs.abstract_field_support
    )

    # Only the maximum is of interest here
    return minmax_per_element.outputs.field_max()


# Scale all fields in the container by a scalar factor.
def get_scaled_field(
    fields_container_: dpf.FieldsContainer, my_factor: float
) -> dpf.FieldsContainer:
    scaled_fc_op = dpf.operators.math.scale_fc(
        fields_container=fields_container_, ponderation=my_factor
    )
    return scaled_fc_op.outputs.fields_container()


# Define the failure criterion.
combined_fc = CombinedFailureCriterion(
    name="Max Stress",
    failure_criteria=[
        MaxStressCriterion(),
    ],
)

# Get the one-sigma results in the layer coordinate system.
raw_stress_op = composite_model.core_model.results.stress()
raw_stress_op.inputs.bool_rotate_to_global(False)
raw_stress_fc = raw_stress_op.eval()
raw_strain_op = composite_model.core_model.results.elastic_strain()
raw_strain_op.inputs.bool_rotate_to_global(False)
raw_strain_fc = raw_strain_op.eval()

# Run the failure analysis and plot the results for one sigma,
# three sigma, using both positive and negative signs.
for factor, title in [(1.0, "1 sigma"), (-1.0, "-1 sigma"), (3.0, "3 sigma"), (-3.0, "-3 sigma")]:

    max_failure_field = run_custom_failure_evaluation(
        combined_fc,
        composite_model,
        get_scaled_field(raw_strain_fc, factor),
        get_scaled_field(raw_stress_fc, factor),
    )
    print(f"Inverse reserve factor for {title}")
    irf_field = max_failure_field[FailureOutput.FAILURE_VALUE]
    irf_field.name = f"{title}: {irf_field.name}"
    composite_model.get_mesh().plot(irf_field)

# %%
# Custom criteria
# ~~~~~~~~~~~~~~~
# You can also implement custom failure criteria for random vibration analysis.
# To do so, pass the scaled stress and strain
# results to the appropriate DPF operators and methods.
#
# For an example of the custom failure criterion implementation, see
# :ref:`sphx_glr_examples_gallery_examples_004_get_material_properties_example.py`.
