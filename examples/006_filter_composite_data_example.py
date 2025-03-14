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
.. _filter_composite_data:

Filter result data by different criteria
----------------------------------------

This example shows how data filtering can be used for custom postprocessing of
layered composites. You can filter strains and stresses by material, layer, or
analysis ply. Filtering by analysis ply is implemented on the server side and
exposed with the :func:`.get_ply_wise_data` function. In this case, the data is
filtered (and reduced) on the server side and only the resulting field is returned
to the client. This is the recommended way to filter data if possible.
For more complex filtering, the data is transferred to the client side and filtered
using numpy functionality.
The examples show filtering data by layer, spot, and node, as well as material
or analysis ply ID. To learn more about how layered result data is organized,
see :ref:`select_indices`.

.. note::

    When using a Workbench project,
    use the :func:`.composite_files_from_workbench_harmonic_analysis`
    method to obtain the input files.

"""

# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of importing dependencies, connecting to the
# DPF server, and retrieving the example files.
#
# Import dependencies.
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import Spot, Sym3x3TensorComponent
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server, version_equal_or_later

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Set up model
# ~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Get result data
# ~~~~~~~~~~~~~~~
# Get the stress field. By default, the stress operator returns the stresses in global coordinates.
# To get the stresses in the material coordinate system, the ``bool_rotate_to_global``
# input is set to ``False``.
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_field_material_coord = stress_operator.get_output(
    pin=0, output_type=dpf.types.fields_container
)[0]

# %%
# Filter data by analysis ply
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~

# %%
# List all available analysis plies.
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

# %%
# The easiest way to filter data by analysis ply is to use the :func:`.get_ply_wise_data` function.
# This function supports different reduction strategies such as computing the average,
# maximum, or minimum over the spot locations.
# It also supports selecting a specific spot (TOP, MID, BOT) directly.
# This example selects the maximum value over all spots for each node and then requests
# the elemental location, which implies averaging over all nodes in an element.
# Using the :func:`.get_ply_wise_data` function has the advantage that all the averaging
# and filtering is done on the server side.
if version_equal_or_later(server, "8.0"):
    elemental_values = get_ply_wise_data(
        field=stress_field_material_coord,
        ply_name="P1L1__ud_patch ns1",
        mesh=composite_model.get_mesh(),
        component=Sym3x3TensorComponent.TENSOR11,
        spot_reduction_strategy=SpotReductionStrategy.MAX,
        requested_location=dpf.locations.elemental,
    )

    composite_model.get_mesh().plot(elemental_values)

# %%
# The results can also be requested in global coordinates. This example gets the stress values in
# the global coordinate system, selects the top spot of a selected ply, and averages the values
# over neighbouring nodes to get nodal results.
stress_operator.inputs.bool_rotate_to_global(True)
stress_field_global_coord = stress_operator.get_output(
    pin=0, output_type=dpf.types.fields_container
)[0]

if version_equal_or_later(server, "8.0"):
    nodal_values = get_ply_wise_data(
        field=stress_field_global_coord,
        ply_name="P1L1__ud_patch ns1",
        mesh=composite_model.get_mesh(),
        component=Sym3x3TensorComponent.TENSOR11,
        spot_reduction_strategy=SpotReductionStrategy.TOP,
        requested_location=dpf.locations.nodal,
    )

    composite_model.get_mesh().plot(nodal_values)


# %%
# Generic client-side filtering
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This example shows how to filter data by layer, spot, and node using the generic filtering on
# the client side.
# This code plots stress values in the material direction for the first node and top spot.

# %%
# Get element information for all elements and show the first one as an example.
element_ids = stress_field_material_coord.scoping.ids
element_infos = [composite_model.get_element_info(element_id) for element_id in element_ids]
element_infos[0]

# %%
# Get filtered data
component = Sym3x3TensorComponent.TENSOR11
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with result_field.as_local_field() as local_result_field:
    element_ids = stress_field_material_coord.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field_material_coord.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices(
            element_info, layers=[element_info.n_layers - 1], nodes=[0], spots=[Spot.TOP]
        )

        value = stress_data[selected_indices][:, component]
        # value needs to be passed as list because dpf does not support numpy
        # slices in the append call.
        local_result_field.append(value.tolist(), element_id)

composite_model.get_mesh().plot(result_field)


# %%
# Filter by material
# ~~~~~~~~~~~~~~~~~~~~~
# Loop over all elements and get the maximum stress in the material direction
# for all plies that have a specific UD material.

ud_material_id = composite_model.material_names["Epoxy Carbon UD (230 GPa) Prepreg"]
component = Sym3x3TensorComponent.TENSOR11

material_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with material_result_field.as_local_field() as local_result_field:
    element_ids = stress_field_material_coord.scoping.ids

    for element_id in element_ids:
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        if ud_material_id in element_info.dpf_material_ids:
            stress_data = stress_field_material_coord.get_entity_data_by_id(element_id)
            selected_indices = get_selected_indices_by_dpf_material_ids(
                element_info, [ud_material_id]
            )

            value = np.max(stress_data[selected_indices][:, component])
            local_result_field.append([value], element_id)

composite_model.get_mesh().plot(material_result_field)

# %%
# Filter by analysis ply on the client side
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Loop over all elements that contain a given ply and plot the maximum stress value
# in the material direction in this ply.
component = Sym3x3TensorComponent.TENSOR11

analysis_ply_info_provider = AnalysisPlyInfoProvider(
    mesh=composite_model.get_mesh(), name="P1L1__ud_patch ns1"
)

ply_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with ply_result_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids

    for element_id in element_ids:
        stress_data = stress_field_material_coord.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices_by_analysis_ply(
            analysis_ply_info_provider, element_info
        )

        value = np.max(stress_data[selected_indices][:, component])
        local_result_field.append([value], element_id)


composite_model.get_mesh().plot(ply_result_field)
