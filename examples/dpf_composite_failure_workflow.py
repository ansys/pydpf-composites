"""
.. _basic_example:

DPF Composite Failure Workflow
------------------------------

Use of native DPF Python interface to configure and run composite failure evaluator.

This example shows how to connect the different dpf operators that are needed to
evaluate composite failure criteria. For simple use cases it is preferable
to use the composite failure operator
(:ref:`sphx_glr_examples_gallery_examples_1_failure_operator_example.py`)
or the composite sampling point operator
(:ref:`sphx_glr_examples_gallery_examples_2_sampling_point_example.py`).
The :ref:`sphx_glr_examples_gallery_examples_6_filter_composite_data_example.py` example shows how
helper functions can be used to obtain composite result data.
"""

#%%
# Script
# ~~~~~~
#
# Load Ansys libraries
#
import ansys.dpf.core as dpf

from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    CuntzeCriterion,
    HashinCriterion,
    HoffmanCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    TsaiHillCriterion,
    TsaiWuCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

#%%
# Configure the combined failure criterion
combined_fc = CombinedFailureCriterion(
    name="My Failure Criteria",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
        TsaiHillCriterion(),
        TsaiWuCriterion(),
        HoffmanCriterion(),
        HashinCriterion(),
        CuntzeCriterion(),
        CoreFailureCriterion(),
        VonMisesCriterion(vme=True, vms=False),
    ],
)


# %%
# Start server and prepare files
server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Initialize DPF model and data sources
model = dpf.Model(composite_files_on_server.rst)
rst_data_source = dpf.DataSources(composite_files_on_server.rst)

eng_data_source = dpf.DataSources()
eng_data_source.add_file_path(composite_files_on_server.engineering_data, "EngineeringData")

composite_definitions_source = dpf.DataSources()
composite_definitions_source.add_file_path(
    composite_files_on_server.composite["shell"].definition, "CompositeDefinitions"
)

# %%
# Set up Mesh Provider
mesh_provider = model.metadata.mesh_provider

# %%
# Set up Material Provider
# The material support provider takes care of mapping the materials in the rst file to
# the materials in the composite definitions.
# The material support contains all the materials from the rst file.
material_support_provider = dpf.Operator("support_provider")
material_support_provider.inputs.property("mat")
material_support_provider.inputs.data_sources(rst_data_source)

# %%
# Get Result Info which
# provides the unit system from the rst file
result_info_provider = dpf.Operator("ResultInfoProvider")
result_info_provider.inputs.data_sources(rst_data_source)

# %%
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
# %%
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

# %%
# Set up the result operators: strains and stresses
# Rotate to global is False because the post-processing engine expects the results to be
# in the element coordinate system ( material coordinate system)
#
strain_operator = dpf.operators.result.elastic_strain()
strain_operator.inputs.data_sources(rst_data_source)
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = dpf.operators.result.stress()
stress_operator.inputs.data_sources(rst_data_source)
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Set up the failure evaluator. Combines the results and evaluates all the failure criteria.
# The output contains the maximum failure criteria for each integration point.
#

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.inputs.configuration(combined_fc.to_json())
failure_evaluator.inputs.materials_container(material_provider.outputs)
failure_evaluator.inputs.strains(strain_operator.outputs.fields_container)
failure_evaluator.inputs.stresses(stress_operator.outputs.fields_container)
failure_evaluator.inputs.mesh(mesh_provider.outputs.mesh)

# %%
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

# %%
# Plot the max and the minimum value for each value
#
value_index = 1
model.metadata.meshed_region.plot(output[value_index])
