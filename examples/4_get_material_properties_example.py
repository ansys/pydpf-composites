"""
.. _material_properties:

Material Properties and Custom Failure Criterion
------------------------------------------------

Access material properties and implement a custom failure criterion.

This example shows how to access constant material properties and how to
implement a custom failure criterion. The failure criterion is computed for
all layers and integration points. Finally, the elemental maximum is computed and shown.

Note: Only constant material properties are currently supported.
"""

#%%
# Script
# ~~~~~~
#
# Import dependencies
import ansys.dpf.core as dpf
import numpy as np

from ansys.dpf.composites import MaterialProperty, get_selected_indices
from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.enums import Sym3x3TensorComponent
from ansys.dpf.composites.example_helper.example_helper import get_continuous_fiber_example_files

#%%
# Start server and load example files
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

#%%
# Set up composite model
composite_model = CompositeModel(composite_files_on_server, server)

#%%
# Get dictionary that maps dpf_material_id to properties
# The creation of the dictionary is currently quite expensive and
# should be done before using the properties in a loop.
# Currently only constant properties are supported.
# For variable material properties, the default value is returned.

material_property = MaterialProperty.strain_limits_ext
property_dict = composite_model.get_constant_property_dict([material_property])


#%%
# Get strain field
strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)
strain_field = strain_operator.get_output(pin=0, output_type=dpf.types.fields_container)[0]


#%%
# Implement a custom failure criterion: basic max strain
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)

with result_field.as_local_field() as local_result_field:
    component = Sym3x3TensorComponent.tensor11

    for element_id in strain_field.scoping.ids:
        strain_data = strain_field.get_entity_data_by_id(element_id)
        element_info = composite_model.get_element_info(element_id)
        element_max = 0
        for layer_index, dpf_material_id in enumerate(element_info.dpf_material_ids):
            tensile_strain_limit_1 = property_dict[dpf_material_id][material_property]
            selected_indices = get_selected_indices(element_info, layers=[layer_index])
            # Tensile max strain criteria in 1 direction
            layer_strain_values = strain_data[selected_indices][:, component.value]
            if tensile_strain_limit_1 > 0:
                layer_max = np.max(layer_strain_values)
                element_max = max(element_max, layer_max / tensile_strain_limit_1)

        # add to output field
        local_result_field.append([element_max], element_id)


composite_model.get_mesh().plot(result_field)
