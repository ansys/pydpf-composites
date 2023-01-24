"""
.. _interlaminar_normal_stress_example:

Interlaminar Normal Stresses
----------------------------

Compute interlaminar normal stresses for layered shells.

This example shows how to enrich the stresses of layered shells by
interlaminar normal stresses, in short INS. INS can be of importance in thick
and curved laminates.

For simple use cases it is preferable to use the composite failure operator
(:ref:`sphx_glr_examples_gallery_examples_1_failure_operator_example.py`)
or the composite sampling point operator
(:ref:`sphx_glr_examples_gallery_examples_2_sampling_point_example.py`). Note, the INS are
computed automatically in these workflows if required. For instance if a 3D failure criterion is
activated.
The :ref:`sphx_glr_examples_gallery_examples_6_filter_composite_data_example.py` example shows how
helper functions can be used to obtain composite result data.

INS are typically not available if layered shell elements are
used. The INS operator recomputes s3 based on the laminate strains, the geometrical curvature and
the lay-up.

"""

# %%
# Script
# ~~~~~~
#
# Load Ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites import CompositeModel, Spot, get_selected_indices
from ansys.dpf.composites.constants import Sym3x3TensorComponent
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a server and get the examples files.
# This will copy the example files into the current working directory.
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "ins")

# %%
# Configure data sources
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Prepare inputs for the INS operator
#
# Rotate to global is False because the post-processing engine expects the results to be
# in the element coordinate system (material coordinate system).

strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Compute interlaminar normal stresses
# """"""""""""""""""""""""""""""""""""
#
# Note: the INS operator stores the stresses in the provided stressed field.
composite_model.add_interlaminar_normal_stresses(
    stresses=stress_operator.outputs.fields_container(),
    strains=strain_operator.outputs.fields_container(),
)

# %%
# Plot s3 stresses
# """"""""""""""""
#
# Get the first stress field
stress_field = stress_operator.outputs.fields_container()[0]

# %%
# Plot max s3 of each element

s3_component = Sym3x3TensorComponent.tensor33
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
# Plot s3 at the mid-plane of a certain ply

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
            element_info, layers=[layer_index], nodes=[0], spots=[Spot.middle]
        )

        # order is bottom, top, mid
        s3 = stress_data[selected_indices, s3_component]

        p8l1_ply_s3_field.append(s3, element_id)

composite_model.get_mesh().plot(p8l1_ply_s3_field)
