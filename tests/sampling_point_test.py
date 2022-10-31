import pathlib
import os

from ansys.dpf.composites.failure_criteria.combined_failure_criterion import (
    CombinedFailureCriterion,
)
from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion
from ansys.dpf.composites.result_definition import ResultDefinition
from ansys.dpf.composites.sampling_point import SamplingPoint

import ansys.dpf.core as dpf


def test_sampling_point(dpf_server):
    """Basic test with a running server"""

    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"
    rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=dpf_server)
    h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=dpf_server)
    material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=dpf_server)

    cfc = CombinedFailureCriterion("max strain & max stress")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())

    rd = ResultDefinition(
        name="my first result definition",
        combined_failure_criterion=cfc,
        composite_definitions=[h5_server_path],
        rst_files=[rst_server_path],
        material_files=[material_server_path],
        element_scope=[3]
    )

    sampling_point = SamplingPoint(name="my first SP",
                                   result_definition=rd,
                                   server=dpf_server)

    results = sampling_point.results()
    print(results)

    sampling_point.plot(False, False, False, False, False)
    print("DONE")
