"""
.. _sampling_point_example:

Sampling Point
--------------

Extract ply-wise laminate properties and results.

The :class:`Sampling Point <ansys.dpf.composites.SamplingPoint>` is feature
to extract through-the-thickness data of laminate. For instance, ply-wise properties
strains and stresses.
Besides that, it implements basic visualization to plot the laminate.

This example uses the :class:`Composite Model <ansys.dpf.composites.CompositeModel>` to
scope a Sampling Point to a certain element and to visualize the laminate.

"""

# %%
# Script
# ~~~~~~
#
# Load Ansys libraries

from ansys.dpf.composites import Spot
from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.example_helper.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)

# %%
# Start server and get files
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Configure the combined failure criterion
def get_combined_failure_criterion() -> CombinedFailureCriterion:
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)

    return CombinedFailureCriterion(
        name="failure of all materials",
        failure_criteria=[max_strain, max_stress, core_failure, von_mises_strain_only],
    )


# %%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Create a sampling point
sampling_point = composite_model.get_sampling_point(
    combined_criteria=get_combined_failure_criterion(), element_id=3
)

# %%
# Plot Results
# """"""""""""
#
# Use pre-configured plots
fig, axes = sampling_point.get_result_plots(
    strain_components=[],  # do not plot strains
    core_scale_factor=0.1,
    spots=[Spot.BOTTOM, Spot.TOP],
    show_failure_modes=True,
)
fig.set_figheight(8)
fig.set_figwidth(12)

# %%
# Plot polar properties
fig, polar_plot = sampling_point.get_polar_plot(["E1", "G12"])

# %%
# Custom plots:
#
# Plots can be easily customized or build from scratch.
# Here, matplotlib is used. An alternative is plotly.
#
# s13 and s23


import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
core_scale_factor = 0.5

sampling_point.add_results_to_plot(
    ax1,
    ["s13", "s23"],
    [Spot.BOTTOM, Spot.TOP],
    core_scale_factor,
    "Out-of-plane shear stresses",
    "MPA",
)
ax1.legend()
plt.rcParams["hatch.linewidth"] = 0.2
plt.rcParams["hatch.color"] = "silver"
sampling_point.add_ply_sequence_to_plot(ax1, core_scale_factor)

# %%
# Plot e12 and e2

interfaces = [Spot.BOTTOM, Spot.TOP]
core_scale_factor = 1.0
indices = sampling_point.get_indices(interfaces)
offsets = sampling_point.get_offsets_by_spots(interfaces, core_scale_factor)
e12 = sampling_point.e12[indices]
e2 = sampling_point.e2[indices]

fig, ax1 = plt.subplots()
plt.rcParams["hatch.linewidth"] = 0.2
plt.rcParams["hatch.color"] = "silver"
line = ax1.plot(e12, offsets, label="e12")
line = ax1.plot(e2, offsets, label="e2")
ax1.set_yticks([])
ax1.legend()
ax1.set_title("e12 and e2")


# %%
# Sample another element
# """"""""""""""""""""""
#
# The element id of the sampling point can be easily changed.
sampling_point.element_id = 4
fig, axes = sampling_point.get_result_plots(
    strain_components=[],  # do not plot strains
    core_scale_factor=0.1,
    spots=[Spot.BOTTOM, Spot.TOP],
    show_failure_modes=True,
)
fig.set_figheight(8)
fig.set_figwidth(12)
