"""
.. _assembly_example:

How to use the composite failure operator for an assembly model
---------------------------------------------------------------

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
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion

server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "assembly_shell")

# %%
# Definition of the combined failure criterion
def get_combined_failure_criterion() -> CombinedFailureCriterion:

    return CombinedFailureCriterion(
        name="failure of all materials",
        failure_criteria=[MaxStressCriterion()],
    )


# %%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server_context.server)
shell_scope = CompositeScope(elements=[1, 2])
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion(), composite_scope=shell_scope
)

#%%
# Plot the max IRF per element
#

irf_field = output_all_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()

composite_files_on_server = get_continuous_fiber_example_files(server_context, "assembly_solid")

# %%
# Setup composite model
composite_model = CompositeModel(composite_files_on_server, server_context.server)
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=get_combined_failure_criterion(),
)

#%%
# Plot the max IRF per element
#

irf_field = output_all_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()
