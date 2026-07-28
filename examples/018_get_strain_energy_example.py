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
.. _ply_wise_strain_energy:

Ply-wise results: strain energy
-------------------------------

Querying and computing ply-wise results is shown in this example using
strain energy :math:`U=\frac{1}{2}*V*\sigma*\epsilon`.
There are other examples which show how to get ply-wise material properties,
strains, and stresses. See
:ref:`sphx_glr_examples_gallery_examples_004_get_material_properties_example.py`,
:ref:`sphx_glr_examples_gallery_examples_005_get_layup_properties_example.py`, and
:ref:`sphx_glr_examples_gallery_examples_006_filter_composite_data_example.py`,

This example shows how to combine raw results (strains and stresses) with layup and model data
such as area and ply-wise thicknesses.

.. note::
    When using a Workbench project,
    use the :func:`.get_composite_files_from_workbench_result_folder`
    method to obtain the input files.

"""

# %%
# Script
# ~~~~~~
#
# Import dependencies
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel, LayerProperty
from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder

# %%
# Start a server and get the examples files.
# This will copy the example files into the current working directory.
server = connect_to_or_start_server()
#composite_files_on_server = get_continuous_fiber_example_files(server, "shell")
composite_files_on_server = get_composite_files_from_workbench_result_folder(r'D:\tmp\WB Projects\critical_layer_index_files\dp0\SYS\MECH')

# %%
# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Pick one analysis ply
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

ply_name = "P1L1__UD.2"

# prepare the data to compute the strain energy
analysis_ply_info_provider = AnalysisPlyInfoProvider(mesh=composite_model.get_mesh(), name=ply_name)

stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_fc = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)
stress_field = stress_fc.get_field_by_time_id(1)

strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)
strain_fc = strain_operator.get_output(pin=0, output_type=dpf.types.fields_container)
strain_field = strain_fc.get_field_by_time_id(1)

area_operator = dpf.operators.geo.elements_volume(
    mesh=composite_model.get_mesh(),
    mesh_scoping=None,
)
area_field = area_operator.outputs.field()

ply_energy_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with ply_energy_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        strain_data = strain_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(element_id)
        selected_indices = get_selected_indices(element_info, layers=[layer_index])

        area = area_field.get_entity_data_by_id(element_id)

        # ply thickness
        thickness = composite_model.get_property_for_all_layers(LayerProperty.THICKNESSES, element_id)[layer_index]

        layer_strain_values = strain_data[selected_indices]
        layer_stress_values = stress_data[selected_indices]
        elemental_strain_energy = 0
        num_int_points = len(layer_strain_values)
        for index, strain_value in enumerate(layer_strain_values):
            elemental_strain_energy += np.dot(strain_value, layer_stress_values[index])

        elemental_strain_energy = elemental_strain_energy / num_int_points * thickness * area
        local_result_field.append([elemental_strain_energy[0] / 2.], element_id)

composite_model.get_mesh().plot(ply_energy_field)

# %%
# Compute the total elemental strain energy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
total_energy_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with total_energy_field.as_local_field() as local_result_field:
    for element_id in composite_model.get_mesh().elements.scoping.ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        strain_data = strain_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        thicknesses = composite_model.get_property_for_all_layers(LayerProperty.THICKNESSES, element_id)

        elemental_strain_energy = 0
        for layer_index in range(element_info.n_layers):
            selected_indices = get_selected_indices(element_info, layers=[layer_index])
            layer_strain_values = strain_data[selected_indices]
            layer_stress_values = stress_data[selected_indices]
            num_int_points = len(layer_strain_values)
            ply_strain_energy = 0
            for index, strain_value in enumerate(layer_strain_values):
                ply_strain_energy += np.dot(strain_value, layer_stress_values[index])

            elemental_strain_energy += ply_strain_energy / num_int_points * thicknesses[layer_index] * area

        local_result_field.append([elemental_strain_energy[0] / 2.], element_id)

composite_model.get_mesh().plot(total_energy_field)
