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

Ply-wise strain energy
----------------------

The implementation of a custom result is shown in this example using
strain energy :math:`U=\\frac{1}{2} \\cdot V \\cdot \\sigma \\cdot \\epsilon`. The first part shows
the computation of the total elemental strain energy, the second part does the
same evaluation but for a specific ply only.

.. note::
    The presented custom implementation is for layered shell elements
    and has been tested only with 4-node shell elements.
    There are a few simplifications in the implementation which may lead to differences
    if compared with the native DPF implementation or Mechanical.
    First, out-of-plane shear forces are ignored. In addition, it is assumed that
    the area weighting factor is the same for each integration point. For irregular elements,
    one would have to compute the Jacobian determinant for each integration point
    to get the exact area weighting factor.

.. note::
    When using a Workbench project,
    use the :func:`.get_composite_files_from_workbench_result_folder`
    method to obtain the input files.

For additional examples that show how to obtain ply-wise material properties,
strains, and stresses, see
:ref:`sphx_glr_examples_gallery_examples_004_get_material_properties_example.py`,
:ref:`sphx_glr_examples_gallery_examples_005_get_layup_properties_example.py`, and
:ref:`sphx_glr_examples_gallery_examples_006_filter_composite_data_example.py`.

"""

# %%
# Script
# ~~~~~~
#
# Import dependencies
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel, LayerProperty
from ansys.dpf.composites.constants import Spot
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfo,
    get_all_analysis_ply_names,
)
from ansys.dpf.composites.select_indices import get_selected_indices, get_spots_from_element_info
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a server and get the examples files.
# This will copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Get Inputs
# ~~~~~~~~~~
# The strains, stresses and volumes (area * thickness) are needed
# for the strain energy computation. These quantities are provided
# by the DPF composites model and the DPF core model.
# Note: the `elements_volume` operator of DPF returns the area instead
# of the volume for (layered) shells.

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
)
area_field = area_operator.outputs.field()


# %%
# Weighting factors
# ~~~~~~~~~~~~~~~~~
#
# This is a helper function to compute the through-the-thickness weighting factor
# of the integration points. Note: MAPDL uses the Simpson integration rule for layered shells
# which weighting factors through-the-thickness are 1/6 for the IP at the bottom and top,
# and 2/3 for the IPs in the middle of the layer.
def weighting_factor(my_element_info: ElementInfo, my_spot: Spot) -> float:

    if not my_element_info.is_shell:
        raise RuntimeError("Weighting factor is only implemented for layered shell elements.")

    if my_element_info.n_spots == 1:
        return 1.0
    if my_spot == Spot.MIDDLE:
        return 2.0 / 3.0
    else:
        return 1.0 / 6.0


# %%
# Strain energy per layer
# ~~~~~~~~~~~~~~~~~~~~~~~
#
# This function returns the strain energy of a single layer.
def layer_wise_strain_energy(
    my_element_info: ElementInfo,
    my_layer_index: int,
    my_element_strains: np.ndarray,
    my_element_stresses: np.ndarray,
    my_thickness: float,
    my_area: float,
) -> float:
    my_strain_energy_density = 0.0
    for spot in get_spots_from_element_info(my_element_info):
        selected_indices = get_selected_indices(
            my_element_info, layers=[my_layer_index], spots=[spot]
        )
        spot_strain_values = my_element_strains[selected_indices]
        spot_stress_values = my_element_stresses[selected_indices]
        wf = weighting_factor(my_element_info, spot)
        for strain_values, stress_values in zip(spot_strain_values, spot_stress_values):
            my_strain_energy_density += np.dot(strain_values, stress_values) * wf

    ply_strain_energy = (
        my_strain_energy_density
        / element_info.number_of_nodes_per_spot_plane
        * my_thickness
        * my_area
        / 2.0
    )
    return ply_strain_energy


# %%
# Compute the total elemental strain energy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Iterator over each element and layer, and build the sum of the strain energy
# over the integration points.
total_energy_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with total_energy_field.as_local_field() as local_result_field:
    # Iterator over all elements of the mesh
    # The model has only layered shell elements and so no filtering is needed here.
    total_strain_energy = 0
    for element_id in composite_model.get_mesh().elements.scoping.ids:
        # Get elemental data
        element_info = composite_model.get_element_info(element_id)
        if element_info is None:
            continue
        thicknesses = composite_model.get_property_for_all_layers(
            LayerProperty.THICKNESSES, element_id
        )
        area = area_field.get_entity_data_by_id(element_id)[0]
        stress_data = stress_field.get_entity_data_by_id(element_id)
        strain_data = strain_field.get_entity_data_by_id(element_id)

        # Iterator over the plies, filter data and compute the strain
        # energy per element
        elemental_strain_energy = 0
        for layer_index in range(element_info.n_layers):
            elemental_strain_energy += layer_wise_strain_energy(
                element_info,
                layer_index,
                strain_data,
                stress_data,
                thicknesses[layer_index],
                area,
            )
        total_strain_energy += elemental_strain_energy
        local_result_field.append([elemental_strain_energy], element_id)

composite_model.get_mesh().plot(total_energy_field)
print(f"Total strain energy: {total_strain_energy} [mJ]")

# %%
# Compute the ply-wise strain energy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Select a ply by name and initialize the AnalysisPlyInfoProvider
# which provides all information of the selected ply. The computation
# of the strain energy is the same as above, just for a single ply.

all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

ply_name = "P1L1__woven_45"
analysis_ply_info_provider = AnalysisPlyInfoProvider(mesh=composite_model.get_mesh(), name=ply_name)

ply_energy_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with ply_energy_field.as_local_field() as local_result_field:
    # Loop over all elements of the analysis ply
    for element_id in analysis_ply_info_provider.property_field.scoping.ids:
        # Get elemental data
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        layer_index = analysis_ply_info_provider.get_layer_index_by_element_id(element_id)

        elemental_strain_energy = layer_wise_strain_energy(
            element_info,
            layer_index,
            strain_field.get_entity_data_by_id(element_id),
            stress_field.get_entity_data_by_id(element_id),
            composite_model.get_property_for_all_layers(LayerProperty.THICKNESSES, element_id)[
                layer_index
            ],
            area_field.get_entity_data_by_id(element_id)[0],
        )
        local_result_field.append([elemental_strain_energy], element_id)

composite_model.get_mesh().plot(ply_energy_field)

# %%
# Native DPF operator for strain energy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# The native DPF operator for strain energy is used to compare the results with
# the above custom implementation. The results differ because of the assumptions mentioned at
# the beginning of the example.
op = dpf.operators.result.stiffness_matrix_energy()  # operator instantiation
op.inputs.data_sources(composite_model.data_sources.result_files)
dpf_strain_energy = op.outputs.fields_container()
dpf_strain_energy[0].plot()
