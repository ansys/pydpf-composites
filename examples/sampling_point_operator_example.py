"""
.. _sampling_point_operator_example:

Basic example for a Sampling Point Operator
-------------------------------------------

Sampling Point Operator returns the through-the-thickness results
of a layered element and lay-up information (ply material, thickness).
This basic example shows how the configure the operator and how to
access the data.

The :ref:`sphx_glr_examples_gallery_examples_sampling_point_example.py` shows
how the sampling point data can be visualized.

"""

# %%
# Load ansys libraries
import matplotlib.pyplot as plt

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_continuous_fiber_example_files,
)
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)

server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "shell")


# %%
# Definition of the combined failure criterion
# --------------------------------------------
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
# Start server
server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "shell")

# %%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server_context.server)

# %%
# Create the sampling point
sampling_point = composite_model.get_sampling_point(
    combined_criteria=get_combined_failure_criterion(), element_id=3
)

# %%
# Query results and plot them
# ---------------------------
results = sampling_point.results

element_label = results[0]["element_label"]
failure_values = results[0]["results"]["failures"]["inverse_reserve_factor"]
failure_modes = results[0]["results"]["failures"]["failure_modes"]
offsets = results[0]["results"]["offsets"]

fig, ax1 = plt.subplots()
ax1.plot(failure_values, offsets)

# add failure modes in the middle of each ply
failure_modes_middle = failure_modes[1::3]
offsets_middle = offsets[1::3]
failure_values_middle = failure_values[1::3]
for index, fm in enumerate(failure_modes_middle):
    ax1.annotate(
        fm,
        xy=(failure_values_middle[index], offsets_middle[index]),
        xytext=(failure_values_middle[index], offsets_middle[index]),
    )

# finalize the plot
ax1.set_title(f"Combined failure criterion of element {element_label}")
ax1.set_xlabel("Inverse Reserve Factor [-]")
ax1.set_ylabel("z-Coordinate [length]")
