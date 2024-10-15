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
.. _interlaminar_normal_stress_example:

Interlaminar normal stresses
----------------------------

This example shows how to enrich the stresses of layered shells by
computing interlaminar normal stresses. Interlaminar normal
stresses can be important in thick and curved laminates.

Because interlaminar normal stresses are typically not available
for layered shell elements, the ``INS`` operator is used to recompute
the ``s3`` result based on the laminate strains, the geometrical
curvature, and the lay-up.

.. note::

    For simple use cases, using the composite failure operator or
    composite sampling point operator is preferable. For examples,
    see :ref:`sphx_glr_examples_gallery_examples_001_failure_operator_example.py`
    and :ref:`sphx_glr_examples_gallery_examples_002_sampling_point_example.py`.
    In these workflows, interlaminar normal stresses are computed automatically
    if required, such as if a 3D failure criterion is activated. Additionally,
    :ref:`sphx_glr_examples_gallery_examples_006_filter_composite_data_example.py`
    shows how helper functions can be used to obtain composite result data.

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
import ansys.dpf.core as dpf
from ansys.dpf.core import unit_systems

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import Spot, Sym3x3TensorComponent
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "ins")

# %%
# Set up model and prepare inputs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(
    composite_files_on_server, server, default_unit_system=unit_systems.solver_mks
)

# %%
# Prepare the inputs for the INS operator.
# ``rotate_to_global`` is ``False`` because the postprocessing engine expects
# the results to be in the element coordinate system (material coordinate system).
strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Compute interlaminar normal stresses
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compute the interlaminar normal stresses.
# The ``INS`` operator stores the stresses in the provided stress field.
composite_model.add_interlaminar_normal_stresses(
    stresses=stress_operator.outputs.fields_container(),
    strains=strain_operator.outputs.fields_container(),
)

# %%
# Plot s3 stresses
# ----------------
# Get the first stress field.
stress_field = stress_operator.outputs.fields_container()[0]

# %%
# Plot the maximum s3 of each element.

s3_component = Sym3x3TensorComponent.TENSOR33
max_s3_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with max_s3_field.as_local_field() as local_max_s3_field:
    element_ids = stress_field.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        # select all stresses from bottom to top of node 0
        selected_indices = get_selected_indices(element_info, nodes=[0])

        # order is bottom, top, mid
        s3 = stress_data[selected_indices, s3_component]

        local_max_s3_field.append([max(s3)], element_id)

composite_model.get_mesh().plot(max_s3_field)

# %%
# Plot s3 at the mid-plane of a certain ply.

analysis_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
selected_ply = "P3L1__Ply.1"

ply_info_provider = AnalysisPlyInfoProvider(composite_model.get_mesh(), selected_ply)
p8l1_ply_s3_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with p8l1_ply_s3_field.as_local_field() as p8l1_ply_s3_field:
    element_ids = ply_info_provider.ply_element_ids()
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        # select all stresses from bottom to top of node 0
        layer_index = ply_info_provider.get_layer_index_by_element_id(element_id)
        selected_indices = get_selected_indices(
            element_info, layers=[layer_index], nodes=[0], spots=[Spot.MIDDLE]
        )

        # order is bottom, top, mid
        s3 = stress_data[selected_indices, s3_component]

        p8l1_ply_s3_field.append(s3, element_id)

composite_model.get_mesh().plot(p8l1_ply_s3_field)
