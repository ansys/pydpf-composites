import pathlib


def test_getting_started():
    """ "
    Caution: This test is identical to the getting_started example.
    Whenever this test needs to be adjusted also the getting started example has to be modified.
    Copy all the code below this comment and replace the code that sets the result_folder
    (by an example results folder).
    Make sure there are no imports except import pathlib outside the current function.
    """

    from ansys.dpf.composites import (
        CompositeModel,
        get_composite_files_from_workbench_result_folder,
    )
    from ansys.dpf.composites.connect_to_or_start_server import connect_to_or_start_server
    from ansys.dpf.composites.enums import FailureOutput
    from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion

    # Folder that opens after clicking "Open Solver Files Directory"
    result_folder = pathlib.Path(__file__).parent / "data" / "workflow_example" / "shell"

    # Create the composite files object that contains
    # the results file, the material properties file and the
    # composite definitions
    composite_files = get_composite_files_from_workbench_result_folder(result_folder)

    # Start the server. By default this will start
    # a new local server and load the composites plugin
    server_context = connect_to_or_start_server()

    # Create a composite model
    composite_model = CompositeModel(composite_files, server_context.server)

    # Evaluate combined failure criterion
    combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
    failure_result = composite_model.evaluate_failure_criteria(combined_failure_criterion)

    irf_field = failure_result.get_field({"failure_label": FailureOutput.failure_value.value})
    irf_field.plot()

    # Show sampling point for element with id/label 1
    element_id = 1
    sampling_point = composite_model.get_sampling_point(
        combined_criteria=combined_failure_criterion, element_id=element_id
    )

    fig, axes = sampling_point.get_result_plots()
    fig.show()
