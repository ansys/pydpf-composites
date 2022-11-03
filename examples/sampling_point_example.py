"""
.. _sampling_point_example:

How to use the Sampling Point wrapper
--------------------------------------

Example how the lay-up data and through-the-thickness results of an
element can be queried and visualized

"""
import os
import pathlib

# %%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites import ResultDefinition, SamplingPoint
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.load_plugin import load_composites_plugin


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


# %%
# Load dpf plugin
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
load_composites_plugin()

# %%
# Specify input files and upload them to the server

TEST_DATA_ROOT_DIR = pathlib.Path(os.environ["REPO_ROOT"]) / "tests" / "data" / "shell"
rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=server)
h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=server)
material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=server)

# %%

# Define the result definition which is used to configure the composite_failure_operator
rd = ResultDefinition(
    "combined failure criteria",
    rst_files=[rst_server_path],
    material_files=[material_server_path],
    composite_definitions=[h5_server_path],
    combined_failure_criterion=get_combined_failure_criterion(),
    element_scope=[3],
)

# %%

# Create the sampling point and update it
sampling_point = SamplingPoint("my first sampling point", rd, server)
sampling_point.update()

# %%

# print the results using preconfigured plots

fig, axes = sampling_point.get_result_plots(
    core_scale_factor=0.1, spots=["bottom", "top"], show_failure_modes=True
)
fig, polar_plot = sampling_point.get_polar_plot(["E1", "G12"])

# custom plots: plot out-of-plane shear stresses

import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
sampling_point.add_results_to_plot(
    ax1, ["s13", "s23"], ["bottom", "top"], 0.5, "Out-of-plane shear stresses"
)
ax1.legend()
plt.rcParams["hatch.linewidth"] = 0.2
sampling_point.add_ply_sequence_to_plot(ax1, 0.5)

# custom plots: extract s12 and s2 at the bottom and top of each ply and plot it

interfaces = ["bottom", "top"]
core_scale_factor = 1.0
indices = sampling_point.get_indices(["bottom", "top"])
offsets = sampling_point.get_offsets(["bottom", "top"], core_scale_factor)
s12 = sampling_point.s12[indices]
s2 = sampling_point.s2[indices]

fig, ax1 = plt.subplots()
plt.rcParams["hatch.linewidth"] = 0.2
line = ax1.plot(s12, offsets, label="s12")
line = ax1.plot(s2, offsets, label="s2")
ax1.set_yticks([])
ax1.legend()
ax1.set_title("S12 and S2")
# sampling_point.add_ply_sequence_to_plot(ax1, core_scale_factor)
