"""
.. _layup_properties_plot:

Get Lay-up Properties
---------------------

Extract elemental layered properties such as thickness and material.

This example shows how to access basic lay-up properties such as layer
thicknesses, angles and analysis ply names. These properties can be queried
very efficiently. To get the full lay-up information of an element including results
consider also :class:`Sampling Point <ansys.dpf.composites.SamplingPoint>`.

Element layered properties are typically used for layer-wise post-processing and
data filtering.

"""

#%%
# Script
# ~~~~~~
#
# Import dependencies
from matplotlib import pyplot as plt
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel, LayerProperty
from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.example_helper.example_helper import get_continuous_fiber_example_files

#%%
# Start server and load example files
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

#%%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server)

#%%
# Get layup properties for all the elements and show the first one as an example
element_id = 1
thicknesses = composite_model.get_property_for_all_layers(LayerProperty.thicknesses, element_id)
angles = composite_model.get_property_for_all_layers(LayerProperty.angles, element_id)
shear_angles = composite_model.get_property_for_all_layers(LayerProperty.shear_angles, element_id)
offset = composite_model.get_element_laminate_offset(element_id)
analysis_plies = composite_model.get_analysis_plies(element_id)


#%%
# Plot lay-up properties
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
