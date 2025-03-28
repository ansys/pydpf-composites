# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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

from ansys.dpf.composites.data_sources import (
    composite_files_from_workbench_harmonic_analysis,
    get_composite_files_from_workbench_result_folder,
)


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

    assert files.result_files == [WORKFLOW_EXAMPLE_ROOT / "file.rst"]
    assert files.engineering_data == WORKFLOW_EXAMPLE_ROOT / "MatML.xml"


def test_get_files_from_result_folder_harmonic(dpf_server):
    WORKFLOW_EXAMPLE_ROOT_HARMONIC = (
        pathlib.Path(__file__).parent
        / "data"
        / "workflow_example"
        / "harmonic"
        / "harmonic_analysis"
    )
    WORKFLOW_EXAMPLE_ROOT_MODAL = (
        pathlib.Path(__file__).parent / "data" / "workflow_example" / "harmonic" / "modal_analysis"
    )

    files = composite_files_from_workbench_harmonic_analysis(
        result_folder_modal=WORKFLOW_EXAMPLE_ROOT_MODAL,
        result_folder_harmonic=WORKFLOW_EXAMPLE_ROOT_HARMONIC,
    )

    assert (
        files.composite["Setup_shell"].definition
        == WORKFLOW_EXAMPLE_ROOT_MODAL / "Setup" / "ACPCompositeDefinitions.h5"
    )

    assert files.result_files == [WORKFLOW_EXAMPLE_ROOT_HARMONIC / "file.rst"]
    assert files.engineering_data == WORKFLOW_EXAMPLE_ROOT_HARMONIC / "MatML.xml"

    # ensure that the setter of RST converts the input into a list
    files.result_files = WORKFLOW_EXAMPLE_ROOT_HARMONIC / "file.rst"
    assert files.result_files == [WORKFLOW_EXAMPLE_ROOT_HARMONIC / "file.rst"]

    # Ensure that the deprecated property rst still works
    # can be removed once .rst is no longer available
    assert files.rst == files.result_files
    files.rst = WORKFLOW_EXAMPLE_ROOT_HARMONIC / "my_new.rst"
    assert files.result_files == [WORKFLOW_EXAMPLE_ROOT_HARMONIC / "my_new.rst"]
    assert files.rst == files.result_files
