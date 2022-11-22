"""
.. _sampling_point_example:

Sampling Point - Processing and visualization of laminate results
-----------------------------------------------------------------

Example how the lay-up and through-the-thickness results of a
layered element can be accessed, processed and visualized.

"""
# %%
# Load ansys libraries

from ansys.dpf.composites import ResultDefinition, SamplingPoint, Spot
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_long_fiber_example_files,
)
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)


# %%
# Definition of the combined failure criterion
def get_combined_failure_criterion() -> CombinedFailureCriterion:
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)

    return CombinedFailureCriterion(
        name="failure of all materials",
        failure_criteria=[max_strain, max_stress, core_failure, von_mises_strain_only],
    )


server_context = connect_to_or_start_server()
composite_files_on_server = get_long_fiber_example_files(server_context, "shell")

# %%
# Configuration of the result definition which is used to configure the composite_failure_operator
rd = ResultDefinition(
    name="combined failure criteria",
    rst_files=[composite_files_on_server.rst],
    material_files=[composite_files_on_server.engineering_data],
    composite_definitions=[composite_files_on_server.composite_definitions],
    combined_failure_criterion=get_combined_failure_criterion(),
    element_scope=[3],
)

# %%
# Create the sampling point and update it
sampling_point = SamplingPoint("my first sampling point", rd, server_context.server)

# %%
# Plot results using preconfigured plots

fig, axes = sampling_point.get_result_plots(
    strain_components=[],  # do not plot strains
    core_scale_factor=0.1,
    spots=[Spot.BOTTOM, Spot.TOP],
    show_failure_modes=True,
)
fig.set_figheight(8)
fig.set_figwidth(12)

# %%
# Plot polar properties using a preconfigured plot

fig, polar_plot = sampling_point.get_polar_plot(["E1", "G12"])

# %%
# Generate a custom plot: plot S13 and S23

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
# Another approach to generate a custom plot

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
