"""
.. _rst_workflow_example:

Failure analysis of an MAPDL (RST) model
----------------------------------------

This example shows the postprocessing of an MAPDL (RST) model with layered elements that was not
preprocessed by ACP. The difference between the RST-
only and ACP-based workflow is that `composite` of the :class:`.ContinuousFiberCompositesFiles`
class is empty, and so the section data are automatically loaded from the RST file.

The engineering data file (XML or ENGD) with the material properties is needed anyway.
Otherwise, the material properties cannot be mapped. You should create it before
solving the model. You can generate the engineering data file with either Ansys Workbench
or ACP (Ansys Composite PrePost) standalone.

.. important::
   The material UUIDs in the engineering data file must be identical
   to the UUIDs in the Mechanical APDL (RST file).

You can set the material UUID in Mechanical APDL with
the ``MP,UVID,<material index>,<value>`` command.

This workflow is supported in 2024 R2 (DPF Server version 8.0) and later.
A few advanced features are not supported with the RST only workflow.
For more information, see :ref:`limitations`.
"""
# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading Ansys libraries, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries.

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    FaceSheetWrinklingCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# %%
# Start a DPF server and copy the example files into the current working directory.
server = connect_to_or_start_server()

# %%
# Get input files (RST and material.engd but skip the ACP layup file).
composite_files_on_server = get_continuous_fiber_example_files(server, "shell", True)
print(composite_files_on_server)

# %%
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
        FaceSheetWrinklingCriterion(),
    ],
)

# %%
# Set up model and evaluate failures
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set up the composite model.

composite_model = CompositeModel(composite_files_on_server, server)

# %%
# Evaluate failures for the entire model
output_all_elements = composite_model.evaluate_failure_criteria(
    combined_criterion=combined_fc,
)
irf_field = output_all_elements.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Create and plot a sampling point
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
sampling_point = composite_model.get_sampling_point(combined_criterion=combined_fc, element_id=2)
sampling_plot = sampling_point.get_result_plots(core_scale_factor=0.1)
sampling_plot.figure.show()
