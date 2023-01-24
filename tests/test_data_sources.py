import pathlib

from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder


def test_get_files_from_result_folder(dpf_server):
    WORKFLOW_EXAMPLE_ROOT = pathlib.Path(__file__).parent / "data" / "workflow_example" / "assembly"

    files = get_composite_files_from_workbench_result_folder(WORKFLOW_EXAMPLE_ROOT)

    assert (
        files.composite["Setup 3_solid"].definition
        == WORKFLOW_EXAMPLE_ROOT / "Setup 3" / "ACPSolidModel_SM.h5"
    )
    assert (
        files.composite["Setup 3_solid"].mapping
        == WORKFLOW_EXAMPLE_ROOT / "Setup 3" / "ACPSolidModel_SM.mapping"
    )

    assert (
        files.composite["Setup 4_shell"].definition
        == WORKFLOW_EXAMPLE_ROOT / "Setup 4" / "ACPCompositeDefinitions.h5"
    )
    assert (
        files.composite["Setup 4_shell"].mapping
        == WORKFLOW_EXAMPLE_ROOT / "Setup 4" / "ACPCompositeDefinitions.mapping"
    )

    assert files.rst == WORKFLOW_EXAMPLE_ROOT / "file.rst"
    assert files.engineering_data == WORKFLOW_EXAMPLE_ROOT / "MatML.xml"
