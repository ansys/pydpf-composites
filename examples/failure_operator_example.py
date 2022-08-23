"""
.. _failure_operator_example:

Example how to use the composite failure operator
-------------------------------------------------

This operator computes the minimum and maximum failure
values and failure modes of a combined failure criterion

"""
import os
import pathlib

# %%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion
from ansys.dpf.composites.failure_criteria import MaxStressCriterion
from ansys.dpf.composites.failure_criteria import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria import CoreFailureCriterion
from ansys.dpf.composites.failure_criteria import VonMisesCriterion

from ansys.dpf.composites import ResultDefinition

# %%
# Definition of the combined failure criterion
def get_combined_failure_criterion():
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)

    return CombinedFailureCriterion(name="failure of all materials",
                                    failure_criteria=[max_strain, max_stress, core_failure, von_mises_strain_only])


# %%
# Load dpf plugin
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
dpf.load_library("libcomposite_operators.so", "composites")
dpf.load_library("libAns.Dpf.EngineeringData.so", "engineeringdata")

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
rd = ResultDefinition("combined failure criteria")
rd.rst_files = [rst_server_path]
rd.material_files = [material_server_path]
rd.composite_definitions = [h5_server_path]
rd.combined_failure_criterion = get_combined_failure_criterion()
rd.element_scope = [1, 2, 3, 4]

fc_op = dpf.Operator("composite::composite_failure_operator")
fc_op.inputs.result_definition(rd.to_json())

output_all_elements = fc_op.outputs.field_max()

#%%
# Plot the max IRF per element
#
failure_value_index = 1
failiure_mode_index = 0

#todo: can we avoid to load the model again?
model = dpf.Model(rst_server_path)
model.metadata.meshed_region.plot(output_all_elements[failure_value_index])

# %%
# Scope failure evaluation to certain

#todo: why is the entire mesh shown?
rd.element_scope = [3, 4]
fc_op.inputs.result_definition(rd.to_json())
output_two_elements = fc_op.outputs.field_max()
model.metadata.meshed_region.plot(output_two_elements[failure_value_index])
