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
.. _layup_properties_plot:

Lay-up properties
-----------------

This example shows how to efficiently extract elemental lay-up properties such as
thickness, angles, and analysis ply names. These are typically used for layer-wise
postprocessing and data filtering.

To get the full layer information of an element, including results,
consider using the :class:`SamplingPoint <.SamplingPoint>` class.

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
from matplotlib import pyplot as plt
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel, LayerProperty
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
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
# Get lay-up properties
# ~~~~~~~~~~~~~~~~~~~~~
# Get lay-up properties for all elements and show the first one as an example.
element_id = 1
thicknesses = composite_model.get_property_for_all_layers(LayerProperty.THICKNESSES, element_id)
angles = composite_model.get_property_for_all_layers(LayerProperty.ANGLES, element_id)
shear_angles = composite_model.get_property_for_all_layers(LayerProperty.SHEAR_ANGLES, element_id)
offset = composite_model.get_element_laminate_offset(element_id)
analysis_plies = composite_model.get_analysis_plies(element_id)


# %%
# Plot lay-up properties
# ~~~~~~~~~~~~~~~~~~~~~~
# Plot basic layer properties (layer thicknesses, angles, and analysis ply names).
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
