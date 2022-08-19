"""
.. _basic_example:

Basic example of setting up a composite failure workflow
----------------------------------------------------------

"""


import json
import os
import pathlib

#%%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion
from ansys.dpf.composites.failure_criteria import MaxStressCriterion
from ansys.dpf.composites.failure_criteria import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria import TsaiHillCriterion
from ansys.dpf.composites.failure_criteria import TsaiWuCriterion
from ansys.dpf.composites.failure_criteria import HoffmanCriterion
from ansys.dpf.composites.failure_criteria import HashinCriterion
from ansys.dpf.composites.failure_criteria import CuntzeCriterion
from ansys.dpf.composites.failure_criteria import CoreFailureCriterion
from ansys.dpf.composites.failure_criteria import VonMisesCriterion

def get_combined_failure_criteria():
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    tsai_hill = TsaiHillCriterion()
    tsai_wu = TsaiWuCriterion()
    hoffman = HoffmanCriterion()
    hashin = HashinCriterion()
    cuntze = CuntzeCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)

    cfc = CombinedFailureCriterion()
    cfc.insert(max_strain)
    cfc.insert(max_stress)
    cfc.insert(tsai_hill)
    cfc.insert(tsai_wu)
    cfc.insert(hoffman)
    cfc.insert(hashin)
    cfc.insert(cuntze)
    cfc.insert(core_failure)
    cfc.insert(von_mises_strain_only)
    return cfc
#%%
# Load dpf plugin
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
dpf.load_library("libcomposite_operators.so", "composites")
dpf.load_library("libAns.Dpf.EngineeringData.so", "engineeringdata")

#%%
# Specify input files and upload them to the server

# Todo make files available for users
TEST_DATA_ROOT_DIR = pathlib.Path(os.environ["REPO_ROOT"]) / "tests" / "data" / "shell"
rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=server)
h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=server)
material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=server)

#%%

model = dpf.Model(rst_server_path)
rst_data_source = dpf.DataSources(rst_server_path)

eng_data_source = dpf.DataSources()
eng_data_source.add_file_path(material_server_path, "EngineeringData")

composite_definitions_source = dpf.DataSources()
composite_definitions_source.add_file_path(h5_server_path, "CompositeDefinitions")

#%%
# Setup Mesh Provider
mesh_provider = dpf.Operator("MeshProvider")
mesh_provider.inputs.data_sources(rst_data_source)

#%%
# Setup Material Provider
# The material support provider takes care of mapping the materials in the rst file to
# the materials in the composite definitions.
# The material support contains all the materials from the rst file.
material_support_provider = dpf.Operator("support_provider")
material_support_provider.inputs.property("mat")
material_support_provider.inputs.data_sources(rst_data_source)

#%%
# Get Result Info
# This is needed provides the unit system from the rst file
result_info_provider = dpf.Operator("ResultInfoProvider")
result_info_provider.inputs.data_sources(rst_data_source)

#%%
# Set up material provider
# Combines the material support the engineering data xml file and the unit_system.
# It's output can be used
# to evaluate material properties
material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
material_provider.inputs.data_sources = eng_data_source
material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
material_provider.inputs.abstract_field_support(
    material_support_provider.outputs.abstract_field_support
)
material_provider.inputs.Engineering_data_file(eng_data_source)
#%%
# Set up the layup provider
# Read the composite definition file and enriches the mesh with the composite layup information.
layup_provider = dpf.Operator("composite::layup_provider_operator")
layup_provider.inputs.mesh(mesh_provider.outputs.mesh)
layup_provider.inputs.data_sources(composite_definitions_source)
layup_provider.inputs.abstract_field_support(
    material_support_provider.outputs.abstract_field_support
)
layup_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
layup_provider.run()

#%%
# Setup the result operators: strains and stresses
# Rotate to global is False because the post-processing engine expects the results to be
# in the element coordinate system ( material coordinate system)
#
strain_operator = dpf.Operator("EPEL")
strain_operator.inputs.data_sources(rst_data_source)
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = dpf.Operator("S")
stress_operator.inputs.data_sources(rst_data_source)
stress_operator.inputs.bool_rotate_to_global(False)

#%%
# Setup the failure evaluator. Combines the results and evaluates all the failure criteria.
# The output contains the maximum failure criteria for each integration point.
#
cfc = get_combined_failure_criteria()

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.inputs.configuration(cfc.to_json_dict())
failure_evaluator.inputs.materials_container(material_provider.outputs)
failure_evaluator.inputs.strains(strain_operator.outputs.fields_container)
failure_evaluator.inputs.stresses(stress_operator.outputs.fields_container)
failure_evaluator.inputs.mesh(mesh_provider.outputs.mesh)

#%%
# Uses the output of the multiple_failure_criteria_operator
# to compute the min and max failure criteria for each element
#
minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.inputs.fields_container(failure_evaluator.outputs.fields_container)
minmax_per_element.inputs.mesh(mesh_provider.outputs.mesh)
minmax_per_element.inputs.abstract_field_support(
    material_support_provider.outputs.abstract_field_support
)

output = minmax_per_element.outputs.field_max()

#%%
# Plot the max and the minimum value for each value
#
value_index = 1
model.metadata.meshed_region.plot(output[value_index])
