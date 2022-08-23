"""
.. _sampling_point_example:

Basic example how to use the sampling point operator which returns
data of the lay-up and failure results
----------------------------------------------------------

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


# %%
# Definition of the combined failure criterion
def get_combined_failure_criterion():
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
# select one element only
rd.element_scope = [3]

sampling_point_op = dpf.Operator("composite::composite_sampling_point_operator")
sampling_point_op.inputs.result_definition(rd.to_json())

# %%
# print the results
results = sampling_point_op.outputs.results()
print(results)
