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
.. _cyclic_symmetry_example:

Cyclic symmetry
---------------

This example shows how to postprocess a cyclic symmetry analysis.
The initial (original) sector can be postprocessed with the same tools
as a standard analysis. This is demonstrated by running a failure analysis,
extracting ply-wise stresses and the implementation of a custom
failure criterion.

The postprocessing of expanded sectors is not yet supported.
"""

# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading the required modules, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries and helper functions.
import ansys.dpf.core as dpf

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput, Sym3x3TensorComponent
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.layup_info import get_all_analysis_ply_names
from ansys.dpf.composites.layup_info.material_properties import MaterialProperty
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files = get_continuous_fiber_example_files(server, "cyclic_symmetry")

# %%
# Create a composite model.
composite_model = CompositeModel(composite_files, server)

# %%
# Evaluate a combined failure criterion.
combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
failure_result = composite_model.evaluate_failure_criteria(combined_failure_criterion)

# %%
# Plot the failure results.
irf_field = failure_result.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Plot ply-wise stresses
# ~~~~~~~~~~~~~~~~~~~~~~
# All functions in PyDPF Composites can be used to
# postprocess the initial (original) sector.

rst_stream = composite_model.core_model.metadata.streams_provider
stress_operator = dpf.operators.result.stress()
stress_operator.inputs.streams_container.connect(rst_stream)
stress_operator.inputs.bool_rotate_to_global(False)
stress_container = stress_operator.outputs.fields_container()

all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

component_s11 = Sym3x3TensorComponent.TENSOR11
stress_field = stress_container[0]
elemental_values = get_ply_wise_data(
    field=stress_field,
    ply_name="P3L1__ModelingPly.1",
    mesh=composite_model.get_mesh(),
    component=component_s11,
    spot_reduction_strategy=SpotReductionStrategy.MAX,
    requested_location=dpf.locations.elemental,
)
composite_model.get_mesh().plot(elemental_values)

# %%
# Custom failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~
# The following code block shows how to implement a custom failure criterion.
# It computes the inverse reserve factor for each element with respect to
# fiber failure. The criterion distinguishes between tension and compression.

# Prepare dict with the material properties
property_xt = MaterialProperty.Stress_Limits_Xt
property_xc = MaterialProperty.Stress_Limits_Xc
property_dict = composite_model.get_constant_property_dict([property_xt, property_xc])

result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with result_field.as_local_field() as local_result_field:
    # Process only the layered elements
    for element_id in composite_model.get_all_layered_element_ids():
        element_info = composite_model.get_element_info(element_id)
        element_irf_max = 0.0
        stress_data = stress_field.get_entity_data_by_id(element_id)
        for layer_index, dpf_material_id in enumerate(element_info.dpf_material_ids):
            xt = property_dict[dpf_material_id][property_xt]
            xc = property_dict[dpf_material_id][property_xc]
            selected_indices = get_selected_indices(element_info, layers=[layer_index])
            # Maximum of fiber failure in tension and compression
            layer_stress_values = stress_data[selected_indices][:, component_s11]
            max_s11 = max(layer_stress_values)
            min_s11 = min(layer_stress_values)
            if xt > 0 and max_s11 > 0:
                element_irf_max = max(max_s11 / xt, element_irf_max)
            if xc < 0 and min_s11 < 0:
                element_irf_max = max(min_s11 / xc, element_irf_max)

        local_result_field.append([element_irf_max], element_id)

composite_model.get_mesh().plot(result_field)

# %%
# Plot deformations on the expanded model
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# You can expand the deformations of the cyclic symmetry model as shown below. 
# The same expansion is possible for strains and stresses. For more information, see `Ansys DPF`_.
# deformations of the cyclic symmetry model. The same can be done
#
# .. _Ansys DPF: https://dpf.docs.pyansys.com/version/stable/

# Get the displacements and expand them
symmetry_option = 2  # fully expand the model
u_cyc = composite_model.core_model.results.displacement()
u_cyc.inputs.read_cyclic(symmetry_option)
# expand the displacements
deformations = u_cyc.outputs.fields_container()[0]

# Get and expand the mesh
mesh_provider = composite_model.core_model.metadata.mesh_provider
mesh_provider.inputs.read_cyclic(symmetry_option)
mesh = mesh_provider.outputs.mesh()
# Plot the expanded deformations
mesh.plot(deformations)
