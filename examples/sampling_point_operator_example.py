"""
.. _sampling_point_operator_example:

How to use the Sampling Point operator
--------------------------------------

Example how the lay-up data and through-the-thickness results of an
element can be queried and visualized

"""
import os
import pathlib
import json
import matplotlib.pyplot as plt

# %%
# Load ansys libraries
import ansys.dpf.core as dpf

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
    "combined failure criteria",
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

# Extract the data and plot it

s13 = results[0]["results"]["stresses"]["s13"]
offsets = results[0]["results"]["offsets"]

plt.plot(s13, offsets, title="S13")
