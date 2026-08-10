# Copyright (C) 2022 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
.. _random_vibration_example:

Postprocess a random vibration analysis
---------------------------------------

A random vibration analysis is post-processed in this example.

.. note::

    When using a Workbench project,
    use the :func:`.composite_files_from_workbench_harmonic_analysis`
    method to obtain the input files.

"""


# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setting up the analysis consists of loading the required modules, connecting to the
# DPF server, and retrieving the example files.
#
# Load Ansys libraries and matplotlib
import os

import ansys.dpf.core as dpf
import matplotlib.pyplot as plt

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FAILURE_LABEL, FailureOutput
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    FailureModeEnum,
    MaxStressCriterion,
    TsaiWuCriterion,
)
from ansys.dpf.composites.layup_info.material_operators import get_material_operators
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.unit_system import get_unit_system

# %%
# Launch DPF server and get input files
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Start a DPF server and copy the example files into the current working directory.
# Getting all the input files for the composite post-processing of a random vibration
# analysis is some manual work. You can open the solver files directory from the solution
# object in Mechanical. There, you'll find the RST file. The engineering data is in the
# same folder (see MatML.xml). The composite files can be found in the first Mechanical analysis system
# of the simulation workflow. For instance, the modal analysis or static analysi in case of pre-stressed
# simulation.
server = connect_to_or_start_server()
# composite_files_on_server = get_continuous_fiber_example_files(server, "random_vibration")
mech_results_folder = (
    r"D:\tmp\WB Projects\Random_Vibration_Basic_Sandwich_Panel_25R1_files\dp0\SYS-4\MECH"
)
rst_file = os.path.join(mech_results_folder, "file.rst")
engd_file = os.path.join(mech_results_folder, "MatML.xml")
acp_h5_file = os.path.join(
    mech_results_folder, "..", "..", "SYS-2", "MECH", "Setup", "ACPCompositeDefinitions.h5"
)
composite_files = ContinuousFiberCompositesFiles(
    files_are_local=True,
    rst=[rst_file],
    composite={
        "shell": CompositeDefinitionFiles(
            mapping=None,
            definition=acp_h5_file,
        )
    },
    engineering_data=engd_file,
)
# composite_files_on_server = get_composite_files_from_workbench_result_folder(mech_results_folder, server)

# %%
# Create a composite model
composite_model = CompositeModel(composite_files, server)


# %%
# Define a failure criterion
combined_fc = CombinedFailureCriterion(
    name="My Failure Criteria",
    failure_criteria=[
        MaxStressCriterion(),
    ],
)

failures = composite_model.evaluate_failure_criteria(combined_fc)
irf_field = failures.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
irf_field.plot()

# %%
# Obtain stresses and strains
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set time scoping (1 for RV)
timeScop = dpf.Scoping()
timeScop.ids = [2]
stress_operator = composite_model.core_model.results.stress.on_all_time_freqs()
stress_operator.inputs.bool_rotate_to_global(False)
stress_operator.inputs.time_scoping(timeScop)
stress_fc = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)
len(stress_fc)
composite_model.get_mesh().plot(stress_fc[1])

strain_operator = composite_model.core_model.results.elastic_strain.on_all_time_freqs()
strain_operator.inputs.bool_rotate_to_global(False)
strain_operator.inputs.time_scoping(timeScop)
