"""
.. _failure_operator_example:

Composite failure analysis
--------------------------

This example shows how to postproces a composite structure by a combined failure criterion.

The failure operator of DPF Composites computes the minimum and maximum failure values
and failure modes of a combined failure criterion. A combined failure criterion is a selection of
failure criteria such as Puck, Tsai-Wu, or face sheet wrinkling. For a list of all
failure criteria, see :ref:`failure_criteria`.

The :class:`Combined Failure Criterion
<.failure_criteria.CombinedFailureCriterion>` class
allows you to assess different type of materials and failure modes at once.
The scoping enables you to evaluate the minimum and maximum failures per element
or select a list of materials or plies.
"""

# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading Ansys libraries, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries.

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.data_source import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# ansys.dpf.composites requires a running DPF server where the composites plugin is loaded.
# this is achieved by calling connect_to_or_start_server() from the server_helpers module.
server = connect_to_or_start_server()
# Define the folder inside Workbench of the analysis with Mechanical
result_folder = r"D:\tmp\my_workbench_project\mechanical"
# Extract the files from the workbench (wb) project and send the to the server.
composite_files = get_composite_files_from_workbench_result_folder(result_folder)

# Configure combined failure criterion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure the combined failure criterion.
combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
        CoreFailureCriterion(),
        VonMisesCriterion(vme=True, vms=False),
    ],
)

# Set up model and evaluate failures
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set up the composite model.
composite_model = CompositeModel(composite_files, server)

# Evaluate failures for the entire model
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Scope failure evaluation to a certain element scope.
output_two_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
    composite_scope=CompositeScope(elements=[1, 3]),
)
irf_field = output_two_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# Scope failure evaluation by plies.
output_woven_plies = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
    composite_scope=CompositeScope(plies=["P1L1__ud_patch ns1"]),
)
irf_field = output_woven_plies.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()
