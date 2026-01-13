# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

import pathlib

import ansys.dpf.core as dpf


def test_getting_started(dpf_server: dpf.server):
    """ "
    Caution: This test is identical to the getting_started example.
    Whenever this test needs to be adjusted also the getting started example has to be modified.
    Copy all the code below this comment and make the following adjustments:
    - replace the code that sets the result_folder (by an example results folder).
    - Make sure no additional imports have been added on the top of the file.
    - Remove the noqa: F401 comment in the import statement
    - Read the comment above the line server = dpf_server and make the corresponding changes.
    - Uncomment the irf_field.plot() line
    """

    from ansys.dpf.composites.composite_model import CompositeModel
    from ansys.dpf.composites.constants import FailureOutput
    from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
    from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
    from ansys.dpf.composites.server_helpers import connect_to_or_start_server  # noqa:  F401

    # Folder that opens after clicking "Open Solver Files Directory"
    result_folder = pathlib.Path(__file__).parent / "data" / "workflow_example" / "shell"

    # Create the composite files object that contains
    # the results file, the material properties file and the
    # composite definitions
    composite_files = get_composite_files_from_workbench_result_folder(result_folder)

    # Start the server. By default this will start
    # a new local server and load the composites plugin

    # In the test we use the dpf server from the fixture.
    # For the getting started example comment the next line and
    # uncomment server = connect_to_or_start_server()
    server = dpf_server
    # server = connect_to_or_start_server()

    # Create a composite model
    composite_model = CompositeModel(composite_files, server)

    # Evaluate combined failure criterion
    combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
    failure_result = composite_model.evaluate_failure_criteria(combined_failure_criterion)

    irf_field = failure_result.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    # Commented because it blocks execution. Uncomment this
    # line when you copy this code to the getting started example
    # irf_field.plot()

    # Show sampling point for element with id/label 1
    element_id = 1
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion, element_id=element_id
    )

    plots = sampling_point.get_result_plots()
    # Commented because it blocks execution. Uncomment this
    # line when you copy this code to the getting started example
    # plots.figure.show()
