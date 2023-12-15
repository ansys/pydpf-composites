from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import FailureOutput
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# ansys.dpf.composites requires a running DPF server where the composites plugin is loaded.
# this is achieved by calling connect_to_or_start_server() from the server_helpers module.
server = connect_to_or_start_server()

# Define path to new Workbench result folder
result_folder = "D:/tmp/ger89_files/dp0/SYS-2/MECH"
# Get composite files from Workbench result folder
composite_files = get_composite_files_from_workbench_result_folder(result_folder)

# Create a composite model with new files
composite_model = CompositeModel(composite_files, server)

# Define a failure criterion
combined_fc = CombinedFailureCriterion(
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
    ],
)

# Begin failure analysis using evaluate_failure_criteria with new files
results = composite_model.evaluate_failure_criteria(combined_criterion=combined_fc)

# Get the field containing the failure values
irf_field = results.get_field({"failure_label": FailureOutput.FAILURE_VALUE})

# Plot the failure values
irf_field.plot()

# Get the sampling point of element 3. Pass the previous defined combined failure criterion
sampling_point = composite_model.get_sampling_point(combined_criterion=combined_fc, element_id=3)
