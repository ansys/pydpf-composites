"""
.. _failure_operator_example:

Composite Failure Analysis
--------------------------

Analyse a composite structure by a combined failure criterion.

The failure operator of DPF Composites computes the minimum and maximum failure values
and failure modes of a combined failure criterion. A combined failure criterion is a selection of
failure criteria such as Puck, Tsai-Wu or Face Sheet Wrinkling. Ref to :ref:`failure_criteria`
to get the full list of failure criteria.

The :class:`Combined Failure Criterion
<ansys.dpf.composites.failure_criteria.CombinedFailureCriterion>`
allows you to assess different type of materials and failure modes at once.
The scoping enables to evaluate of the min and max failure per element,
or to select a list of materials or plies.
"""
# %%
# Script
# ~~~~~~
#
# Load ansys libraries

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
from ansys.dpf.composites.enums import FailureOutput
from ansys.dpf.composites.example_helper.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)

server = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server, "shell")

# %%
# Configure the combined failure criterion

combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
        CoreFailureCriterion(),
        VonMisesCriterion(vme=True, vms=False),
    ],
)

# %%
# Set up composite model
composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Failure evaluation for the entire model
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=combined_fc,
)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()

# %%
# Scope failure evaluation to a certain element scope
output_two_elements = composite_model.evaluate_failure_criteria(
    combined_criteria=combined_fc,
    composite_scope=CompositeScope(elements=[1, 3]),
)
irf_field = output_two_elements.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()

# %%
# Scope by plies
output_woven_plies = composite_model.evaluate_failure_criteria(
    combined_criteria=combined_fc,
    composite_scope=CompositeScope(plies=["P1L1__ud_patch ns1"]),
)
irf_field = output_woven_plies.get_field({"failure_label": FailureOutput.failure_value.value})
irf_field.plot()
