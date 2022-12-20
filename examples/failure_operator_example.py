"""
.. _failure_operator_example:

How to use the composite failure operator
-----------------------------------------

This operator computes the minimum and maximum failure
values and failure modes of a combined failure criterion

"""
# %%
# Load ansys libraries

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.enums import FailureOutput
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
# Setup composite model
composite_model = CompositeModel(composite_files_on_server)
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion(),
)

#%%
# Plot the max IRF per element
#

irf_field = output_all_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()

# %%
# Scope failure evaluation to certain element scope
output_two_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion(),
    composite_scope=CompositeScope(elements=[1, 3]),
)
irf_field = output_two_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()

# %%
# Scope by plies
output_woven_plies = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion(),
    composite_scope=CompositeScope(plies=["P1L1__ud_patch ns1"]),
)
irf_field = output_woven_plies.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()
