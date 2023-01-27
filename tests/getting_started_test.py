import pathlib

import ansys.dpf.core as dpf

from ansys.dpf.composites.example_helper import upload_continuous_fiber_composite_files_to_server


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

    # In the test we use the dpf server and upload the files to the server.
    # For the getting started example comment the next two lines and
    # uncomment serer = connect_to_or_start_server()
    server = dpf_server
    if not server.local_server:
        composite_files = upload_continuous_fiber_composite_files_to_server(composite_files, server)
    # server = connect_to_or_start_server()

    # Create a composite model
    composite_model = CompositeModel(composite_files, server)

    # Evaluate combined failure criterion
    combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
    failure_result = composite_model.evaluate_failure_criteria(combined_failure_criterion)

    irf_field = failure_result.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    # Commented because it blocks execution. Uncomment this
    # line when you copy this code the getting started example
    # irf_field.plot()

    # Show sampling point for element with id/label 1
    element_id = 1
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion, element_id=element_id
    )

    sampling_point.get_result_plots()
