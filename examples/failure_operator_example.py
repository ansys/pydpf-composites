"""
.. _failure_operator_example:

Composite failure operator
--------------------------

This operator computes the minimum and maximum failure values and failure modes
of a combined failure criterion. A combined failure criterion is a selection of
failure criteria such as Puck, Tsai-Wu, Face Sheet Wrinkling...

The combined failure criterion allows you to assess different type of materials
and failure modes at once. The scoping enables to evaluate of the min and max
failure per element, or to select a list of materials or plies.

"""
# %%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites import ResultDefinition
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
# Define the result definition which is used to configure the composite_failure_operator
# Process all elements
rd = ResultDefinition(
    name="combined failure criteria",
    rst_files=[composite_files_on_server.rst],
    material_files=[composite_files_on_server.engineering_data],
    composite_definitions=[composite_files_on_server.composite_definitions],
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
