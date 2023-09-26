"""
.. _filter_composite_data:

Filter result data by different criteria
----------------------------------------

This example show how data filtering can be used for custom postprocessing of
layered composites. You can filter strains and stresses by material, layer, or
analysis ply. The example filters data by layer, spot, and node, as well as material
or analysis ply ID. To learn more about how layered result data is organized,
see :ref:`select_indices`.
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
from ansys.dpf.composites.layup_info import (
    AnalysisPlyInfoProvider,
    get_all_analysis_ply_names,
    get_dpf_material_id_by_analysis_ply_map,
)
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

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
# Get the stress field.
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_field = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)[0]

# %%
# Get element information for all elements and show the first one as an example.
element_ids = stress_field.scoping.ids
element_infos = [composite_model.get_element_info(element_id) for element_id in element_ids]
element_infos[0]

# %%
# Plot result data
# ~~~~~~~~~~~~~~~~
# For the top layer, plot stress values in the material direction for the first node and top spot.
component = Sym3x3TensorComponent.TENSOR11
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with result_field.as_local_field() as local_result_field:
    element_ids = stress_field.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices(
            element_info, layers=[element_info.n_layers - 1], nodes=[0], spots=[Spot.TOP]
        )

        value = stress_data[selected_indices][:, component]
        local_result_field.append(value, element_id)

composite_model.get_mesh().plot(result_field)

# %%
# List analysis plies
# ~~~~~~~~~~~~~~~~~~~
# List all available analysis plies.
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

# %%
# Plot results
# ~~~~~~~~~~~~
# Loop all elements that contain a given ply and plot the maximum stress value
# in the material direction in this ply.
component = Sym3x3TensorComponent.TENSOR11

analysis_ply_info_provider = AnalysisPlyInfoProvider(
    mesh=composite_model.get_mesh(), name="P1L1__ud_patch ns1"
)
ply_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with ply_result_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids

    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices_by_analysis_ply(
            analysis_ply_info_provider, element_info
        )

        value = np.max(stress_data[selected_indices][:, component])
        local_result_field.append([value], element_id)


composite_model.get_mesh().plot(ply_result_field)

# %%
# Loop all elements and get the maximum stress in the material direction
# for all plies that have a material with DPF material ID.
# Note: It is not possible to get a DPF material ID for a
# given material name. It is only possible to get a DPF material
# ID from an analysis ply.
material_names = get_dpf_material_id_by_analysis_ply_map(
    composite_model.get_mesh(), data_source_or_streams_provider=composite_model.data_sources.rst
)
ud_material_id = material_map["P1L1__ud_patch ns1"]
component = Sym3x3TensorComponent.TENSOR11

material_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with material_result_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids

    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None

        selected_indices = get_selected_indices_by_dpf_material_ids(element_info, [ud_material_id])

        value = np.max(stress_data[selected_indices][:, component])
        local_result_field.append([value], element_id)

composite_model.get_mesh().plot(material_result_field)
