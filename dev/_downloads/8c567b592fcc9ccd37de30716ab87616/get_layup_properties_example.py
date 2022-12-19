"""
.. _layup_properties_plot:

Get Layup Properties
----------------------------------------------------------

This example shows how to access basic layup properties such as layer
thicknesses, angles and analysis ply names. These properties can be queried
very efficiently. To get the full layup information of an element including results
consider also the sampling point operator
(:ref:`sphx_glr_examples_gallery_examples_sampling_point_example.py`)
"""

#%%
# Import dependencies
import ansys.dpf.core as dpf
from matplotlib import pyplot as plt
import numpy as np

from ansys.dpf.composites.add_layup_info_to_mesh import (
    add_layup_info_to_mesh,
    get_composites_data_sources,
)
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_continuous_fiber_example_files,
)
from ansys.dpf.composites.layup_info import LayupPropertiesProvider

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
# Get layup properties for all the elements and show the first one as an example
properties_provider = LayupPropertiesProvider(
    layup_provider=layup_operators.layup_provider, mesh=mesh
)
element_id = 1
thicknesses = properties_provider.get_layer_thicknesses(element_id)
offset = properties_provider.get_element_laminate_offset(element_id)
angles = properties_provider.get_layer_angles(element_id)
shear_angles = properties_provider.get_layer_shear_angles(element_id)
analysis_plies = properties_provider.get_analysis_plies(element_id)


#%%
# Plot of layup properties
y_coordinates = offset + np.cumsum(thicknesses)
y_centers = y_coordinates - thicknesses / 2

fig, ax1 = f, ax = plt.subplots(figsize=(6, 10))

for y_coordinate in y_coordinates:
    ax1.axhline(y=y_coordinate, color="k")

for angle, shear_angle, y_coordinate, analysis_ply in zip(
    angles, shear_angles, y_centers, analysis_plies
):
    ax1.annotate(
        f"Angle={angle}°, Shear Angle={shear_angle}°, {analysis_ply}",
        xy=(0.1, y_coordinate),
        xytext=(0.1, y_coordinate),
    )

fig.show()
