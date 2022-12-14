"""
.. _filter_composite_data:

Filter result data by different criteria
----------------------------------------------------------

Filter data by layer, spot and node as well as material or analysis_ply id.
Refer to :ref:`select_indices` to learn more about how layered result data is organized.

"""

#%%
# Import dependencies
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites import (
    AnalysisPlyInfoProvider,
    get_element_info_provider,
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)
from ansys.dpf.composites.add_layup_info_to_mesh import (
    add_layup_info_to_mesh,
    get_composites_data_sources,
)
from ansys.dpf.composites.enums import Spot, Sym3x3TensorComponent
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_continuous_fiber_example_files,
)
from ansys.dpf.composites.layup_info import (
    get_all_analysis_ply_names,
    get_dpf_material_id_by_analyis_ply_map,
)

#%%
# Start server and load example files

server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "shell")

#%%
# Setup Mesh Provider
model = dpf.Model(composite_files_on_server.rst)
mesh_provider = model.metadata.mesh_provider

#%%
# Reads the composite definition file and enriches the mesh with the composite layup information.
composites_data_sources = get_composites_data_sources(composite_files_on_server)
add_layup_info_to_mesh(mesh=mesh_provider.outputs.mesh(), data_sources=composites_data_sources)


#%%
# Get example stress field and mesh
stress_operator = dpf.Operator("S")
stress_operator.inputs.data_sources(composites_data_sources.rst)
stress_operator.inputs.bool_rotate_to_global(False)
stress_field = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)[0]
mesh = mesh_provider.outputs.mesh()

#%%
# Get element infos for all the elements and show the first one as an example
element_info_provider = get_element_info_provider(mesh, composites_data_sources.rst)
element_ids = stress_field.scoping.ids
element_infos = [element_info_provider.get_element_info(element_id) for element_id in element_ids]

element_infos[0]

#%%
# Plot stress values in material direction for the top layer, first node and "top" spot
component = Sym3x3TensorComponent.tensor11
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with result_field.as_local_field() as local_result_field:
    element_ids = stress_field.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = element_info_provider.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices(
            element_info, layers=[element_info.n_layers - 1], nodes=[0], spots=[Spot.TOP]
        )

        value = stress_data[selected_indices][:, component.value]
        local_result_field.append(value, element_id)

mesh.plot(result_field)

#%%
# List all the available analysis plies
all_ply_names = get_all_analysis_ply_names(mesh)
all_ply_names

#%%
# Loop all elements that contain a given ply and plot the maximum stress value
# in material direction in that ply
component = Sym3x3TensorComponent.tensor11

analysis_ply_info_provider = AnalysisPlyInfoProvider(mesh=mesh, name="P1L1__ud_patch ns1")
ply_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with ply_result_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids

    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = element_info_provider.get_element_info(element_id)
        assert element_info is not None
        selected_indices = get_selected_indices_by_analysis_ply(
            analysis_ply_info_provider, element_info
        )

        value = np.max(stress_data[selected_indices][:, component.value])
        local_result_field.append([value], element_id)


mesh.plot(ply_result_field)

#%%
# Loop all elements and get maximum stress in material direction
# for all plies that have the material with dpf_material_id.
# Note: It is currently not possible to get a dpf_material_id for a
# given material name. It is only possible
# to get the dpf_material_id from an analysis ply
material_map = get_dpf_material_id_by_analyis_ply_map(
    mesh, data_source_or_streams_provider=composites_data_sources.rst
)
ud_material_id = material_map["P1L1__ud_patch ns1"]
component = Sym3x3TensorComponent.tensor11

material_result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with material_result_field.as_local_field() as local_result_field:
    element_ids = analysis_ply_info_provider.property_field.scoping.ids

    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = element_info_provider.get_element_info(element_id)
        assert element_info is not None

        selected_indices = get_selected_indices_by_dpf_material_ids(element_info, [ud_material_id])

        value = np.max(stress_data[selected_indices][:, component.value])
        local_result_field.append([value], element_id)


mesh.plot(material_result_field)
