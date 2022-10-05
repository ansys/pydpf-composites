"""
.. _failure_operator_example:

How to use the composite failure operator
-----------------------------------------

This operator computes the minimum and maximum failure
values and failure modes of a combined failure criterion

"""
import os
import pathlib

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
# Process all elements
rd = ResultDefinition(
    name="combined failure criteria",
    rst_files=[rst_server_path],
    material_files=[material_server_path],
    composite_definitions=[h5_server_path],
    combined_failure_criterion=get_combined_failure_criterion(),
)

fc_op = dpf.Operator("composite::composite_failure_operator")
fc_op.inputs.result_definition(rd.to_json())

output_all_elements = fc_op.outputs.fields_containerMax()

#%%
# Plot the max IRF per element
#
failure_value_index = 1
failiure_mode_index = 0

irf_field = output_all_elements[failure_value_index]
irf_field.plot()

# %%
# Scope failure evaluation to certain
rd.element_scope = [1, 3]
fc_op.inputs.result_definition(rd.to_json())
output_two_elements = fc_op.outputs.fields_containerMax()
irf_field = output_two_elements[failure_value_index]
irf_field.plot()

# %%
# Scope by plies
rd.element_scope = []
rd.ply_scope = ["P1L1__ud_patch ns1"]
fc_op.inputs.result_definition(rd.to_json())
output_woven_plies = fc_op.outputs.fields_containerMax()
irf_field = output_woven_plies[failure_value_index]
irf_field.plot()
