"""
.. _material_properties:

Get Material Properties and evaluate basic failure criterion
-------------------------------------------------------------

This example shows how to access constant material properties and
evaluate a basic strain limit failure criterion. Note: Only constant material properties
are currently supported.
"""

#%%
# Import dependencies
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites import MaterialProperty, get_constant_property_dict, get_selected_indices
from ansys.dpf.composites.add_layup_info_to_mesh import (
    add_layup_info_to_mesh,
    get_composites_data_sources,
)
from ansys.dpf.composites.enums import Sym3x3TensorComponent
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_continuous_fiber_example_files,
)
from ansys.dpf.composites.layup_info import get_element_info_provider

#%%
# Start server and load example files

server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "shell")

#%%
# Setup Mesh Provider
model = dpf.Model(composite_files_on_server.rst)
mesh_provider = model.metadata.mesh_provider
mesh = mesh_provider.outputs.mesh()

#%%
# Reads the composite definition file and enriches the mesh with the composite layup information.
composites_data_sources = get_composites_data_sources(composite_files_on_server)
layup_operators = add_layup_info_to_mesh(mesh=mesh, data_sources=composites_data_sources)

#%%
# Get dictionary that maps dpf material id to properties
# The creation of the dictionary is currently quite expensive and
# should be done before using the properties in a loop.
# Currently only constant properties are supported.
# For variable material properties, the default value is returned.

material_property = MaterialProperty.Strain_Limits_eXt

property_dict = get_constant_property_dict(
    material_property=material_property,
    materials_provider=layup_operators.material_operators.material_provider,
    data_source_or_streams_provider=composites_data_sources.rst,
    mesh=mesh,
)
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

#%%
# Get example strain field
strain_operator = dpf.Operator("EPEL")
strain_operator.inputs.data_sources(composites_data_sources.rst)
strain_operator.inputs.bool_rotate_to_global(False)
strain_field = strain_operator.get_output(pin=0, output_type=dpf.types.fields_container)[0]


#%%
# Evaluate basic max strain failure criterion

element_info_provider = get_element_info_provider(mesh, composites_data_sources.rst)

with result_field.as_local_field() as local_result_field:
    component = Sym3x3TensorComponent.tensor11

    for element_id in strain_field.scoping.ids:
        strain_data = strain_field.get_entity_data_by_id(element_id)
        element_info = element_info_provider.get_element_info(element_id)
        element_max = 0
        for layer_index, material_id in enumerate(element_info.material_ids):
            tensile_strain_limit_1 = property_dict[material_id]
            selected_indices = get_selected_indices(element_info, layers=[layer_index])
            # Tensile max strain criteria in 1 direction
            layer_strain_values = strain_data[selected_indices][:, component.value]
            if tensile_strain_limit_1 > 0:
                layer_max = np.max(layer_strain_values)
                element_max = max(element_max, layer_max / tensile_strain_limit_1)

        # Compute Maximum over all layers and add to output field
        local_result_field.append([element_max], element_id)


mesh.plot(result_field)
