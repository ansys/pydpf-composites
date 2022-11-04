"""
.. _sampling_point_operator_example:

Basic example for a Sampling Point Operator
-------------------------------------------

Sampling Point Operator returns the through-the-thickness results
of a layered element and lay-up information (ply material, thickness).
This basic example shows how the configure the operator and how to
access the data.

"""
import json
import os
import pathlib

# %%
# Load ansys libraries
import ansys.dpf.core as dpf
import matplotlib.pyplot as plt

from ansys.dpf.composites import ResultDefinition
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
    "Combined Failure Criteria",
    rst_files=[rst_server_path],
    material_files=[material_server_path],
    composite_definitions=[h5_server_path],
    combined_failure_criterion=get_combined_failure_criterion(),
    element_scope=[3],
)

sampling_point_op = dpf.Operator("composite::composite_sampling_point_operator")
sampling_point_op.inputs.result_definition(rd.to_json())

# %%

# get the results and convert into JSON Dict

results = json.loads(sampling_point_op.outputs.results())

# %%

# Extract failure values and modes and plot them
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
ax1.set_title(f"{rd.name} of element {element_label}")
ax1.set_xlabel("Inverse Reserve Factor [-]")
ax1.set_ylabel("z-Coordinate [length]")
