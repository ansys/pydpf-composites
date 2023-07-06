import pathlib

import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.constants import FailureOutput
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
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    min_id = irfs.scoping.ids[np.argmin(irfs.data)]
    max_id = irfs.scoping.ids[np.argmax(irfs.data)]

    composite_scope = CompositeScope(elements=[min_id, max_id])
    max_container = composite_model.evaluate_failure_criteria(cfc, composite_scope)
    max_irfs = max_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
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
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    assert len(irfs.data) == 2
    assert irfs.data[0] == pytest.approx(1.4792790331384016, 1e-8)
    assert irfs.data[1] == pytest.approx(1.3673715033617213, 1e-8)


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
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    modes = failure_container.get_field({"failure_label": FailureOutput.FAILURE_MODE})

    if version_older_than(dpf_server, "7.0"):
        # the old implementation did not allow to distinguish between plies of the different parts.
        # So both plies select the shell and solid elements.
        assert len(irfs.data) == 6
        assert irfs.data == pytest.approx(
            np.array([0.66603946, 0.66603946, 3.24925826, 0.52981576, 3.24925826, 0.52981576]),
            abs=1e-3,
        )
        assert modes.data == pytest.approx(
            np.array([310.0, 310.0, 310.0, 222.0, 310.0, 212.0]), abs=0.1
        )
    else:
        # ply scoping is now part specific thanks to the labels
        assert len(irfs.data) == 4
        assert irfs.data == pytest.approx(
            np.array([0.14762838, 0.14762838, 3.24925826, 3.24925826]), abs=1e-3
        )
        assert modes.data == pytest.approx(np.array([222, 212, 310, 310]), abs=0.1)


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
    irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    modes = failure_container.get_field({"failure_label": FailureOutput.FAILURE_MODE})
    assert len(irfs.data) == 2
    assert len(modes.data) == 2
    assert irfs.data == pytest.approx(np.array([0.49282684, 0.32568454]), abs=1e-3)
    assert modes.data == pytest.approx(np.array([222.0, 222.0]), abs=1e-1)


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
        irfs = failure_container.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
        modes = failure_container.get_field({"failure_label": FailureOutput.FAILURE_MODE})
        assert len(irfs.data) == 4
        assert max(irfs.data) == pytest.approx(expected_max_irf, abs=1e-6)
