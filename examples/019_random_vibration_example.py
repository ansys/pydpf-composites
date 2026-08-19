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

r"""
.. _random_vibration_example:

Random vibration analysis
-------------------------

This example shows how to run a failure analysis for a random vibration analysis using the Max
Stress criterion. The failure factors are computed with respect to the one sigma and three sigma 
values.

The documentation of Mechanical about random vibration analysis states that the directional
results from a Power Spectral Density (PSD) analysis are statistical in nature, and so they
cannot be combined in the usual way. For example the X, Y,
and Z displacements cannot be combined to get the magnitude of the total displacement.
The same holds for other derived quantities such as strains and stresses.
This means that most of the failure criteria, such as Puck and Hashin, are not applicable since they
combine stress components to compute the failure factors.
For the same reason, it is also important to highlight that the strain and stress tensors should
not be rotated. Luckily, the results of a random vibration analysis are given in the layer (material)
coordinate system.

Taking that into account, the max strain and stress can be used because the failure values are computed
for each component (e1, e2, s1, etc.) separately.

Another point to consider is that the solution provided by Mechanical is always positive and
corresponds to the one sigma values. But the results could be positive or negative, and the strength values
of orthotropic materials are typically different for tension and compression. So, failure factors with respect to
the negative scaled results must be computed as well. The results for two and three sigma can be computed
by just scaling the one sigma results.

.. note::

    The interpretation of the one sigma is that 68.3% of the time the response will be less than these values.
    The response will be less than the two sigma values 95.45% of the time and three sigma values 99.73% of the time.

.. note::

    When using Ansys Workbench, the user has to manually extract
    the paths of the input files since it is a nested analysis.
    The RST and material file (MatML.XML) can be found in the solver files directory
    of the random vibration analysis.
    The composite definitions file(s) can be found in the first Mechanical analysis
    system of the simulation workflow (e.g., ..\\..\\SYS-2\\MECH\\Setup\\ACPCompositeDefinitions.h5").
    Importantly, also pass the mapping files to ContinuousFiberCompositesFiles
    if the model is an assembly of several Mechanical models. The mapping files (*.mapping)
    can be found in the folder where the ACPCompositeDefinitions.h5 file is located.

"""


# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading the required modules, connecting to the
# DPF server, and retrieving the example files.
import os

import ansys.dpf.core as dpf

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Launch DPF server and get input files
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "random_vibration")

# %%
# Create a composite model
composite_model = CompositeModel(composite_files_on_server, server)


# %%
# Failure Evaluation
# ~~~~~~~~~~~~~~~~~~
# Implements a custom failure evaluation workflow since strains and stresses
# must be scaled. It uses the multiple_failure_criteria_operator to compute all failure
# criteria for the scaled results, and the minmax_per_element_operator to extract the
# minimum and maximum over all failure criteria, layers and integration points.
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


# %%
# Helper function to compute the scaled results
def get_scaled_field(
    fields_container_: dpf.FieldsContainer, my_factor: float
) -> dpf.FieldsContainer:
    scaled_fc_op = dpf.operators.math.scale_fc(
        fields_container=fields_container_, ponderation=my_factor
    )
    return scaled_fc_op.outputs.fields_container()


# %%
# Definition of the failure criterion
combined_fc = CombinedFailureCriterion(
    name="Max Stress",
    failure_criteria=[
        MaxStressCriterion(),
    ],
)

# %%
# Get the results (one sigma) in the layer coordinate system
raw_stress_op = composite_model.core_model.results.stress()
raw_stress_op.inputs.bool_rotate_to_global(False)
raw_stress_fc = raw_stress_op.eval()
raw_strain_op = composite_model.core_model.results.elastic_strain()
raw_strain_op.inputs.bool_rotate_to_global(False)
raw_strain_fc = raw_strain_op.eval()


# %%
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
# Custom failure criteria can be implemented for random vibration analysis
# as well. In this case the scaled strain and stress results have to be passed
# to the according DPF operators and methods.
# An example of an implementation of a custom failure criterion is shown in
# :ref:`sphx_glr_examples_gallery_examples_004_get_material_properties_example.py`.
