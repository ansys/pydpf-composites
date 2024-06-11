# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FAILURE_LABEL, FailureOutput
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    HashinCriterion,
    MaxStressCriterion,
)
from ansys.dpf.composites.layup_info import get_all_analysis_ply_names
from ansys.dpf.composites.server_helpers._versions import version_older_than

from .helper import get_basic_shell_files

SEPARATOR = "::"


def test_composite_model_element_scope(dpf_server, data_files):
    """Ensure that the element IDs of the scope can be of any type (e.g. np.int)"""
    composite_model = CompositeModel(data_files, server=dpf_server)
    cfc = CombinedFailureCriterion("max stress", failure_criteria=[MaxStressCriterion()])

    composite_scope = CompositeScope(elements=[1, 3])
    failure_container = composite_model.evaluate_failure_criteria(cfc, composite_scope)
    irfs = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
    min_id = irfs.scoping.ids[np.argmin(irfs.data)]
    max_id = irfs.scoping.ids[np.argmax(irfs.data)]

    composite_scope = CompositeScope(elements=[min_id, max_id])
    max_container = composite_model.evaluate_failure_criteria(cfc, composite_scope)
    max_irfs = max_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
    assert len(max_irfs.data) == 2
    assert max_irfs.get_entity_data_by_id(min_id)[0] == pytest.approx(min(irfs.data), 1e-8)
    assert max_irfs.get_entity_data_by_id(max_id)[0] == pytest.approx(max(irfs.data), 1e-8)


def test_composite_model_named_selection_scope(dpf_server, data_files, distributed_rst):
    """Ensure that the scoping by Named Selection is supported"""
    if distributed_rst:
        # TODO: remove once backend issue #856638 is resolved
        pytest.xfail("The mesh property provider operator does not yet support distributed RST.")

    composite_model = CompositeModel(data_files, server=dpf_server)

    ns_name = "NS_ELEM"
    assert ns_name in composite_model.get_mesh().available_named_selections
    ns_scope = composite_model.get_mesh().named_selection(ns_name)
    assert list(ns_scope.ids) == [2, 3]

    cfc = CombinedFailureCriterion("max stress", failure_criteria=[MaxStressCriterion()])

    scope = CompositeScope(named_selections=[ns_name])
    failure_container = composite_model.evaluate_failure_criteria(cfc, scope)
    irfs = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
    assert len(irfs.data) == 2
    assert irfs.get_entity_data_by_id(2) == pytest.approx(1.4792790331384016, 1e-8)
    assert irfs.get_entity_data_by_id(3) == pytest.approx(1.3673715033617213, 1e-8)


def test_composite_model_ply_scope(dpf_server):
    """
    Verify that ply scope is fully supported.

    If ply scope is set, then the failure evaluation is limited to the selected plies.
    """

    files = get_composite_files_from_workbench_result_folder(
        pathlib.Path(__file__).parent / "data" / "workflow_example" / "assembly"
    )

    solid_label = "Setup 3_solid"
    shell_label = "Setup 4_shell"

    composite_model = CompositeModel(files, server=dpf_server)

    if version_older_than(dpf_server, "7.0"):
        analysis_plies = []
        for label in [solid_label, shell_label]:
            analysis_plies.extend(get_all_analysis_ply_names(composite_model.get_mesh(label)))
        ply_ids = ["P1L1__core", f"P1L1__woven_45.2"]
    else:
        analysis_plies = get_all_analysis_ply_names(composite_model.get_mesh())
        ply_ids = [f"{solid_label}::P1L1__core", f"{shell_label}::P1L1__woven_45.2"]

    for ply in ply_ids:
        assert ply in analysis_plies

    cfc = CombinedFailureCriterion(
        "combined", failure_criteria=[MaxStressCriterion(), CoreFailureCriterion()]
    )

    scope = CompositeScope(plies=ply_ids)
    failure_container = composite_model.evaluate_failure_criteria(cfc, scope)
    irfs = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
    modes = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_MODE})

    if version_older_than(dpf_server, "7.0"):
        # the old implementation did not allow to distinguish between plies of the different parts.
        # So both plies select the shell and solid elements.
        expected_irfs_by_element_id = {
            1: 0.66603946,
            2: 0.66603946,
            7: 3.24925826,
            8: 3.24925826,
            9: 0.52981576,
            10: 0.52981576,
        }

        expected_modes_by_element_id = {1: 310.0, 2: 310.0, 7: 310.0, 8: 310.0, 9: 212.0, 10: 222.0}
        assert len(irfs.data) == 6
        for element_id in irfs.scoping.ids:
            assert expected_irfs_by_element_id[element_id] == pytest.approx(
                irfs.get_entity_data_by_id(element_id), abs=1e-3
            )
            assert expected_modes_by_element_id[element_id] == pytest.approx(
                modes.get_entity_data_by_id(element_id), abs=0.1
            )

    else:
        # ply scoping is now part specific thanks to the labels
        assert len(irfs.data) == 4

        expected_irfs_by_element_id = {
            1: 0.14762838,
            2: 0.14762838,
            7: 3.24925826,
            8: 3.24925826,
        }

        expected_modes_by_element_id = {
            1: 222,
            2: 212,
            7: 310,
            8: 310,
        }

        for element_id in irfs.scoping.ids:
            assert irfs.get_entity_data_by_id(element_id) == pytest.approx(
                expected_irfs_by_element_id[element_id], abs=1e-3
            )
            assert modes.get_entity_data_by_id(element_id) == pytest.approx(
                expected_modes_by_element_id[element_id], abs=1e-1
            )


def test_composite_model_named_selection_and_ply_scope(dpf_server, data_files, distributed_rst):
    """Verify scoping by Named Selection in combination with plies."""
    if distributed_rst:
        # TODO: remove once backend issue #856638 is resolved
        pytest.xfail("The mesh property provider operator does not yet support distributed RST.")

    composite_model = CompositeModel(data_files, server=dpf_server)

    ns_name = "NS_ELEM"
    assert ns_name in composite_model.get_mesh().available_named_selections
    ns_scope = composite_model.get_mesh().named_selection(ns_name)
    assert list(ns_scope.ids) == [2, 3]

    ply_ids = ["P1L1__woven_45.2", "P1L1__ud.2"]
    analysis_plies = get_all_analysis_ply_names(composite_model.get_mesh())
    for ply in ply_ids:
        assert ply in analysis_plies

    cfc = CombinedFailureCriterion(
        "combined", failure_criteria=[HashinCriterion(), MaxStressCriterion()]
    )

    scope = CompositeScope(named_selections=[ns_name], plies=ply_ids)
    failure_container = composite_model.evaluate_failure_criteria(cfc, scope)
    irfs = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
    modes = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_MODE})
    assert len(irfs.data) == 2
    assert len(modes.data) == 2
    expected_irfs_by_id = {2: 0.49282684, 3: 0.32568454}
    expected_modes_by_id = {2: 222.0, 3: 222.0}
    for element_id in irfs.scoping.ids:
        assert irfs.get_entity_data_by_id(element_id) == pytest.approx(
            expected_irfs_by_id[element_id], abs=1e-3
        )
        assert modes.get_entity_data_by_id(element_id) == pytest.approx(
            expected_modes_by_id[element_id], abs=1e-1
        )


def test_composite_model_time_scope(dpf_server):
    """Verify time scoping."""
    files = get_basic_shell_files(two_load_steps=True)
    composite_model = CompositeModel(files, server=dpf_server)
    cfc = CombinedFailureCriterion(
        "combined",
        failure_criteria=[
            MaxStressCriterion(s1=True, s2=True, s3=True, s12=True, s13=True, s23=True)
        ],
    )
    # Note: the expected irf at time 1.5 is not the average of the other twos because the
    # load cases are different with respected to the force components.
    time_id_and_expected_max_irf = {
        1.0: 1.4792790998492324,
        1.5: 0.75120980930142467,
        2.0: 0.09834992555064767,
    }

    for time, expected_max_irf in time_id_and_expected_max_irf.items():
        scope = CompositeScope(time=time)
        failure_container = composite_model.evaluate_failure_criteria(cfc, scope)
        irfs = failure_container.get_field({FAILURE_LABEL: FailureOutput.FAILURE_VALUE})
        assert len(irfs.data) == 4
        assert max(irfs.data) == pytest.approx(expected_max_irf, abs=1e-6)


def test_ply_wise_scoping_in_assembly_with_imported_solid_model(dpf_server):
    """Ensure that the ply-wise scoping works in combination with the reference surface plot."""
    if version_older_than(dpf_server, "9.0"):
        pytest.xfail(
            "The post-processing of imported solid models is supported with version 9.0 (2025 R1) or later."
        )

    result_folder = pathlib.Path(__file__).parent / "data" / "assemby_imported_solid_model"

    composite_files = get_composite_files_from_workbench_result_folder(result_folder)

    # Create a composite model
    composite_model = CompositeModel(composite_files, dpf_server)

    plies = [
        "Setup 2_shell::P1L1__ModelingPly.2",
        "Setup_solid::P1L1__ModelingPly.2",
        "Setup 3_solid::P1L1__ModelingPly.1",
    ]

    # Evaluate combined failure criterion
    combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
    failure_result = composite_model.evaluate_failure_criteria(
        combined_criterion=combined_failure_criterion, composite_scope=CompositeScope(plies=plies)
    )

    # check the on reference surface data
    for failure_output in [
        FailureOutput.FAILURE_VALUE_REF_SURFACE,
        FailureOutput.FAILURE_MODE_REF_SURFACE,
        FailureOutput.MAX_GLOBAL_LAYER_IN_STACK,
        FailureOutput.MAX_LOCAL_LAYER_IN_ELEMENT,
        FailureOutput.MAX_SOLID_ELEMENT_ID,
    ]:
        field = failure_result.get_field({FAILURE_LABEL: failure_output})
        assert field.size == 21
