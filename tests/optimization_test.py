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

"""Optimization tests independent of a DPF or ACP server."""

from dataclasses import replace
import json
from types import SimpleNamespace

import numpy as np
import pytest

from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.layup_info import AnalysisPlyInfo
from ansys.dpf.composites.optimization import (
    ACPAdditionTemplate,
    AdditionRule,
    AngleBounds,
    ClassicalLaminateEvaluator,
    DiscreteAngles,
    InvalidDesign,
    Laminate,
    LaminateChangeSet,
    LaminateDesignSpace,
    LaminateForces,
    LaminateOptimizationProblem,
    LaminateResponse,
    LoadCase,
    Material,
    PlyRule,
    PyACPAdapter,
    SpatialPlyExtentOptimizer,
    scipy_differential_evolution,
    scipy_minimize,
)


def material(name="A", **kwargs):
    return Material(
        name,
        "uuid-" + name,
        "regular",
        {
            "E1": 100.0,
            "E2": 10.0,
            "E3": 10.0,
            "G12": 5.0,
            "G13": 5.0,
            "G23": 4.0,
            "nu12": 0.25,
            "nu13": 0.25,
            "nu23": 0.3,
        },
        **kwargs,
    )


def laminate(name="one", angles=(0, 45, 45, 0), **kwargs):
    return Laminate(
        name=name,
        plies=tuple(
            AnalysisPlyInfo.from_local_ply(
                id=f"p{i}", material_name="A", angle=a, thickness=1.0,
                global_ply_number=i + 1,
            )
            for i, a in enumerate(angles)
        ),
        materials=(material(), material("B")),
        load_cases=kwargs.pop("load_cases", (LoadCase("load", LaminateForces(Nx=1)),)),
        unit_system="SI",
        offset=-len(angles) / 2,
        **kwargs,
    )


def candidate(space, **updates):
    values = list(space.initial)
    for name, value in updates.items():
        values[next(i for i, v in enumerate(space.variables) if v.name == name)] = value
    return values


def evaluate(point, case):
    mass = sum(p.thickness * (2 if p.material_name == "A" else 1) for p in point.plies)
    irf = abs(case.forces.Nx) / point.thickness
    return LaminateResponse(mass, (irf,) * len(point.plies))


def test_sampling_point_snapshot_and_clt_round_trip():
    original = laminate()
    document = original.to_clt_dict(original.load_cases[0])
    document["materials"][0]["id"] = "opaque-id"
    for ply in document["layup"]["analysis_plies"]:
        ply["material"] = "opaque-id"
    before = json.dumps(document)
    copied = Laminate.from_sampling_point(SimpleNamespace(results=[document]), name="snapshot")
    assert copied.name == "snapshot"
    assert isinstance(copied.plies[0], AnalysisPlyInfo)
    assert copied.plies == original.plies
    assert copied.load_cases[0].forces.Nx == 1
    assert json.dumps(document) == before
    assert copied.to_clt_dict(copied.load_cases[0])["layup"]["num_analysis_plies"] == 4
    with pytest.raises(TypeError):
        copied.materials[0].properties["E1"] = 200


def test_analysis_ply_info_keeps_nominal_and_local_thickness_distinct():
    info = AnalysisPlyInfo.from_local_ply(
        id="draped-ply",
        material_name="A",
        angle=12,
        thickness=0.8,
        nominal_thickness=1.0,
        global_ply_number=17,
    )
    assert info.nominal_thickness == 1.0
    assert info.local_thickness == 0.8
    assert info.thickness == 0.8
    assert info.global_ply_number == 17


@pytest.mark.parametrize("missing", ["materials", "laminate_forces", "unit_system"])
def test_old_sampling_point_output_is_rejected(missing):
    document = laminate().to_clt_dict(laminate().load_cases[0])
    del document[missing]
    with pytest.raises(ValueError, match="CLT input"):
        Laminate.from_sampling_point(document)


def test_explicit_load_cases_and_shell_validation():
    document = laminate().to_clt_dict(laminate().load_cases[0])
    del document["laminate_forces"]
    cases = (LoadCase("other", LaminateForces(Ny=10)),)
    assert Laminate.from_sampling_point([document], load_cases=cases).load_cases == cases
    document["element_type"] = "solid"
    with pytest.raises(ValueError, match="shell"):
        Laminate.from_sampling_point(document, load_cases=cases)


@pytest.mark.parametrize("angles", [(0, 45, 45, 0), (0, 45, 90, 45, 0), (0, 180)])
def test_symmetric_even_odd_and_equivalent_angles(angles):
    assert laminate(angles=angles).is_symmetric()
    space = LaminateDesignSpace([laminate(angles=angles)], symmetric=True)
    assert space.decode(space.initial)[0].is_symmetric()


def test_symmetry_is_not_balance():
    point = laminate(angles=(45, -45))
    assert not point.is_symmetric()
    with pytest.raises(ValueError, match="not symmetric"):
        LaminateDesignSpace([point], symmetric=True)


def test_mirrored_angle_and_material_variables():
    space = LaminateDesignSpace(
        [laminate()],
        symmetric=True,
        default_rule=PlyRule(angles=DiscreteAngles((0, 45, 90)), materials=("A", "B")),
    )
    assert len(space.variables) == 4
    decoded = space.decode(candidate(space, **{"p0.angle": 2, "p0.material": 1}))[0]
    assert decoded.plies[0].angle == decoded.plies[-1].angle == 90
    assert decoded.plies[0].material_name == decoded.plies[-1].material_name == "B"
    assert decoded.is_symmetric()


def test_discrete_angle_domain_projects_out_of_domain_initial_angles():
    point = laminate(angles=(135, 180))
    space = LaminateDesignSpace(
        [point], default_rule=PlyRule(angles=DiscreteAngles((0, 15, 30, 45, 60, 75, 90)))
    )
    projected = space.decode(space.initial)[0]
    assert [ply.angle for ply in projected.plies] == [90, 0]
    assert [ply.angle for ply in point.plies] == [135, 180]


def test_symmetric_pair_removal_and_center_removal():
    space = LaminateDesignSpace(
        [laminate(angles=(0, 45, 90, 45, 0))],
        symmetric=True,
        default_rule=PlyRule(removable=True),
        minimum_plies=2,
    )
    decoded = space.decode(candidate(space, **{"p0.active": 0, "p2.active": 0}))[0]
    assert [p.id for p in decoded.plies] == ["p1", "p3"]
    assert decoded.is_symmetric()
    assert decoded.offset == -1


@pytest.mark.parametrize("position", [0, 1, 2])
def test_symmetric_additions_are_pairs_and_order_is_mirrored(position):
    space = LaminateDesignSpace(
        [laminate()],
        symmetric=True,
        additions=[
            AdditionRule(
                "skin", ("A", "B"), 0.5, DiscreteAngles((0, 15, 45)), max_count=2
            )
        ],
    )
    values = candidate(
        space,
        **{
            "added:skin:0.active": 1,
            "added:skin:0.position": position,
            "added:skin:1.active": 1,
            "added:skin:1.position": 2 - position,
            "added:skin:0.angle": 1,
            "added:skin:1.angle": 2,
        },
    )
    point = space.decode(values)[0]
    assert point.is_symmetric()
    assert len(point.plies) == 8
    assert len({p.id for p in point.plies}) == 8
    assert all(p.thickness > 0 for p in point.plies)
    assert point.offset == -3


def test_reordering_preserves_center_and_mirrored_identity():
    space = LaminateDesignSpace(
        [laminate(angles=(0, 45, 90, 45, 0))],
        symmetric=True,
        allow_reordering=True,
    )
    point = space.decode(candidate(space, **{"p0.order": 2, "p1.order": 0}))[0]
    assert [p.id for p in point.plies] == ["p1", "p0", "p2", "p4", "p3"]
    assert point.is_symmetric()


def test_shared_edits_keep_noncommon_local_patches():
    first = laminate()
    second = replace(laminate("two"), plies=tuple(p for p in first.plies if p.id != "p1"))
    rule = PlyRule(angles=AngleBounds(-30, 30), angle_mode="offset", removable=True)
    space = LaminateDesignSpace([first, second], ply_rules={"p0": rule})
    decoded = space.decode(candidate(space, **{"p0.angle": 15}))
    assert all(p.plies[0].angle == 15 for p in decoded)
    assert decoded[0].plies[1] == first.plies[1]
    assert "p1" not in space.common_ply_ids
    local_rule = PlyRule(angles=AngleBounds(-30, 30), angle_mode="offset")
    local_space = LaminateDesignSpace([first, second], ply_rules={"p1": local_rule})
    local_decoded = local_space.decode(candidate(local_space, **{"p1.angle": 10}))
    assert local_decoded[0].plies[1].angle == first.plies[1].angle + 10
    assert [p.id for p in local_decoded[1].plies] == [p.id for p in second.plies]


def test_different_local_orientations_require_offsets():
    first = laminate()
    second = replace(
        laminate("two"), plies=tuple(replace(p, angle=p.angle + 10) for p in first.plies)
    )
    with pytest.raises(ValueError, match="offset"):
        LaminateDesignSpace([first, second], default_rule=PlyRule(AngleBounds(-90, 90)))
    space = LaminateDesignSpace(
        [first, second],
        default_rule=PlyRule(AngleBounds(-20, 20), angle_mode="offset"),
        symmetric=True,
    )
    points = space.decode(candidate(space, **{"p0.angle": 15}))
    assert points[0].plies[0].angle == 15
    assert points[1].plies[0].angle == 25
    assert all(p.is_symmetric() for p in points)


def test_symmetry_checks_fixed_local_plies_and_rules():
    first = laminate()
    with pytest.raises(ValueError, match="both mirror"):
        LaminateDesignSpace([first], symmetric=True, ply_rules={"p0": PlyRule(removable=True)})
    with pytest.raises(ValueError, match="identical edit"):
        LaminateDesignSpace(
            [first],
            symmetric=True,
            ply_rules={
                "p0": PlyRule(removable=True),
                "p3": PlyRule(),
            },
        )
    asymmetric = replace(
        first,
        plies=first.plies[:-1] + (replace(first.plies[-1], local_thickness=2),),
    )
    with pytest.raises(ValueError, match="not symmetric"):
        LaminateDesignSpace([asymmetric], symmetric=True)


def test_material_nominal_thickness_policy():
    first = laminate(angles=(0, 0))
    space = LaminateDesignSpace(
        [first],
        symmetric=True,
        materials=[material(nominal_thickness=1), material("B", nominal_thickness=0.5)],
        default_rule=PlyRule(materials=("A", "B"), use_material_thickness=True),
    )
    decoded = space.decode(candidate(space, **{"p0.material": 1}))[0]
    assert decoded.thickness == 1
    assert decoded.offset == -0.5


@pytest.mark.parametrize("values", [[0.5, 0], [np.nan, 0], [-1, 0], [0], [1, 5]])
def test_bad_numerical_candidates(values):
    space = LaminateDesignSpace([laminate(angles=(0, 0))], default_rule=PlyRule(removable=True))
    with pytest.raises(ValueError):
        space.decode(values)


def test_minimum_plies_and_fixed_constraint_shape():
    space = LaminateDesignSpace([laminate(angles=(0, 0))], default_rule=PlyRule(removable=True))
    problem = LaminateOptimizationProblem(space, evaluate, constraints=[lambda *_: -1])
    valid = problem.evaluate(space.initial)
    invalid = problem.evaluate([0, 0])
    assert invalid.invalid_reason
    assert len(invalid.constraints) == len(valid.constraints) == 2
    assert invalid.max_violation == float("inf")


def test_all_load_cases_weights_cache_and_custom_constraints():
    cases = (LoadCase("one", LaminateForces(Nx=1)), LoadCase("two", LaminateForces(Nx=6)))
    first = laminate(load_cases=cases, weight=3)
    second = laminate("two", angles=(0, 0), weight=1)
    calls = []

    def evaluator(point, case):
        calls.append((point.name, case.name))
        return evaluate(point, case)

    space = LaminateDesignSpace([first, second])
    problem = LaminateOptimizationProblem(space, evaluator, constraints=[lambda *_: -0.25])
    assert problem.objective(space.initial) == 7
    assert problem.constraint_values(space.initial) == (-0.75, 0.5, -0.5, -0.25)
    assert len(calls) == 3
    assert problem.evaluate(space.initial).max_violation == 0.5


def test_callable_driver_uses_best_feasible_and_rechecks_it():
    space = LaminateDesignSpace(
        [laminate(angles=(0, 0, 0, 0))],
        symmetric=True,
        default_rule=PlyRule(removable=True),
    )
    problem = LaminateOptimizationProblem(space, evaluate)

    def optimizer(p, token):
        assert token == 42
        assert p.objective([0, 1]) == 4
        p.evaluate([0, 0])  # cheaper but structurally invalid
        return {"x": space.initial, "success": False, "message": "budget exhausted"}

    result = problem.optimize(optimizer, token=42)
    assert result.feasible and not result.solver_success
    assert result.best.objective == 4
    assert len(result.changes.changes) == 2
    assert result.evaluations[-1].values == (0, 1)
    json.dumps(result.to_dict(), allow_nan=False)


def test_infeasible_result_is_not_reported_as_feasible():
    point = laminate(load_cases=(LoadCase("load", LaminateForces(Nx=100)),))
    problem = LaminateOptimizationProblem(LaminateDesignSpace([point]), evaluate)
    result = problem.optimize(lambda *_: pytest.fail("No variables: driver must not run"))
    assert not result.feasible
    assert result.best.max_violation > 0


def test_backend_errors_propagate():
    def broken(*_):
        raise RuntimeError("backend failed")

    problem = LaminateOptimizationProblem(LaminateDesignSpace([laminate()]), broken)
    with pytest.raises(RuntimeError, match="backend failed"):
        problem.evaluate([])


def test_scipy_mixed_integer_driver():
    pytest.importorskip("scipy")
    space = LaminateDesignSpace(
        [laminate(angles=(0, 0, 0, 0))],
        symmetric=True,
        default_rule=PlyRule(materials=("A", "B")),
    )
    problem = LaminateOptimizationProblem(space, evaluate)
    result = problem.optimize(
        scipy_differential_evolution, seed=2, maxiter=5, popsize=5, polish=False
    )
    assert result.feasible
    assert result.best.objective == 4
    assert all(p.material_name == "B" for p in result.best.laminates[0].plies)
    with pytest.raises(ValueError, match="continuous"):
        scipy_minimize(problem)


def test_scipy_continuous_driver():
    pytest.importorskip("scipy")
    space = LaminateDesignSpace(
        [laminate(angles=(0, 0))],
        symmetric=True,
        default_rule=PlyRule(angles=AngleBounds(-45, 45)),
    )
    problem = LaminateOptimizationProblem(
        space,
        evaluate,
        objective=lambda points, _: (points[0].plies[0].angle - 15) ** 2,
    )
    result = problem.optimize(scipy_minimize)
    assert result.feasible
    assert result.best.laminates[0].plies[0].angle == pytest.approx(15, abs=1e-5)


def in_plane_criterion():
    return CombinedFailureCriterion(
        failure_criteria=[MaxStressCriterion(s3=False, s13=False, s23=False)]
    )


def test_dpf_evaluator_operator_contract(monkeypatch):
    from ansys.dpf.composites.optimization import _evaluator

    connections = {}

    class Inputs:
        def __getattr__(self, key):
            return lambda value: connections.update({key: value})

    class FakeOperator:
        def __init__(self, name, server):
            assert name == "composite::classical_laminate_theory_operator"
            assert server == "server"
            self.inputs = Inputs()

        def get_output(self, *_):
            return json.dumps(
                {
                    "mass_per_unit_area": 8,
                    "results": {
                        "failures": {
                            "inverse_reserve_factor": [0.25] * 4,
                            "failure_modes": [0] * 4,
                        }
                    },
                }
            )

    monkeypatch.setattr(_evaluator, "Operator", FakeOperator)
    evaluator = ClassicalLaminateEvaluator(
        SimpleNamespace(_server="server", outputs="materials"), in_plane_criterion()
    )
    point = laminate()
    response = evaluator(point, point.load_cases[0])
    assert response.max_irf == 0.25
    assert connections["compute_mass_per_area"] is True
    definition = json.loads(connections["failure_criteria_definition"])
    assert definition["version"] == 1
    assert "max_stress" in definition["failure_criteria_definition"]["criteria"]
    assert json.loads(connections["layup_definition"])["laminate_forces"]["Nx"] == 1


def test_dpf_evaluator_rejects_unsupported_criteria_and_uncovered_materials():
    with pytest.raises(ValueError, match="out-of-plane"):
        ClassicalLaminateEvaluator(
            SimpleNamespace(),
            CombinedFailureCriterion(failure_criteria=[MaxStressCriterion(s3=True)]),
        )
    evaluator = ClassicalLaminateEvaluator(SimpleNamespace(), in_plane_criterion())
    point = laminate()
    core = replace(material(), ply_type="honeycomb_core")
    point = replace(point, materials=(core, material("B")))
    with pytest.raises(ValueError, match="no applicable"):
        evaluator(point, point.load_cases[0])


def acp_ply(angle=0):
    fabric = SimpleNamespace(material=object(), thickness=1)
    return SimpleNamespace(
        ply_angle=angle,
        ply_material=fabric,
        number_of_layers=1,
        thickness_type="nominal",
        global_ply_nr=1,
        active=True,
    )


def angle_result():
    point = laminate(angles=(0, 0))
    space = LaminateDesignSpace([point], symmetric=True, default_rule=PlyRule(AngleBounds(-45, 45)))
    problem = LaminateOptimizationProblem(
        space, evaluate, objective=lambda points, _: -points[0].plies[0].angle
    )
    return problem.optimize(lambda _: {"x": [15], "success": True})


def test_pyacp_dry_run_and_apply():
    updates = []
    bindings = {"p0": acp_ply(), "p1": acp_ply()}
    adapter = PyACPAdapter(SimpleNamespace(update=lambda: updates.append(True)), bindings)
    result = angle_result()
    plan = adapter.apply(result)
    assert len(plan) == 2
    assert bindings["p0"].ply_angle == 0
    assert not updates
    adapter.apply(result, dry_run=False)
    assert bindings["p0"].ply_angle == bindings["p1"].ply_angle == 15
    assert len(updates) == 1


def test_pyacp_preflight_detects_stale_and_ambiguous_bindings():
    ply = acp_ply()
    with pytest.raises(ValueError, match="same modeling ply"):
        PyACPAdapter(None, {"p0": ply, "p1": ply})
    adapter = PyACPAdapter(None, {"p0": ply, "p1": acp_ply()})
    ply.ply_angle = 30
    with pytest.raises(ValueError, match="changed since"):
        adapter.apply(angle_result())


def test_pyacp_removal_is_nondestructive():
    point = laminate(angles=(0, 0, 0, 0))
    space = LaminateDesignSpace(
        [point], default_rule=PlyRule(removable=True), offset_policy="bottom"
    )
    problem = LaminateOptimizationProblem(space, evaluate)
    result = problem.optimize(lambda _: {"x": [0, 1, 1, 1], "success": True})
    bindings = {p.id: acp_ply() for p in point.plies}
    adapter = PyACPAdapter(SimpleNamespace(update=lambda: None), bindings)
    adapter.apply(result, dry_run=False)
    assert not bindings["p0"].active
    assert bindings["p1"].active


def test_change_set_retains_reordering_even_without_property_changes():
    point = laminate()
    changed = replace(point, plies=tuple(reversed(point.plies)))
    changes = LaminateChangeSet.between([point], [changed])
    assert not changes.changes
    assert changes.to_dict()["optimized"][0]["plies"][0]["id"] == "p3"


def test_shared_symmetry_on_different_complete_local_stacks():
    first = laminate()
    second = replace(laminate("two"), plies=(first.plies[0], first.plies[-1]), offset=-1)
    space = LaminateDesignSpace(
        [first, second],
        symmetric=True,
        default_rule=PlyRule(AngleBounds(0, 90)),
        additions=[AdditionRule("skin", ("A",), 0.5)],
    )
    points = space.decode(candidate(space, **{"p0.angle": 30, "added:skin:0.active": 1}))
    assert [len(p.plies) for p in points] == [6, 4]
    assert all(p.is_symmetric() for p in points)
    assert points[0].plies[2] == first.plies[1]  # fixed local ply retained
    assert points[0].plies[0].id == points[1].plies[0].id == "added:skin:0"


def test_center_gap_addition_ids_have_bottom_top_order():
    space = LaminateDesignSpace(
        [laminate()],
        symmetric=True,
        additions=[AdditionRule("middle", ("A",), 0.5, max_count=2)],
    )
    point = space.decode(
        candidate(
            space,
            **{
                "added:middle:0.active": 1,
                "added:middle:0.position": 2,
                "added:middle:1.active": 1,
                "added:middle:1.position": 2,
            },
        )
    )[0]
    assert [p.id for p in point.plies[2:6]] == [
        "added:middle:0",
        "added:middle:1",
        "added:middle:1:mirror",
        "added:middle:0:mirror",
    ]


def test_additions_only_with_no_common_plies():
    first = laminate(angles=(0, 0))
    second = replace(
        laminate("two", angles=(0, 0)),
        plies=(
            AnalysisPlyInfo.from_local_ply(
                id="other0", material_name="A", angle=0, thickness=1
            ),
            AnalysisPlyInfo.from_local_ply(
                id="other1", material_name="A", angle=0, thickness=1
            ),
        ),
    )
    with pytest.raises(ValueError, match="No common"):
        LaminateDesignSpace([first, second])
    space = LaminateDesignSpace(
        [first, second],
        symmetric=True,
        additions=[AdditionRule("new", ("A",), 1)],
    )
    assert not space.common_ply_ids
    assert all(len(p.plies) == 4 for p in space.decode([1, 0, 0, 0]))


def test_symmetry_removal_of_every_ply_is_invalid():
    space = LaminateDesignSpace(
        [laminate(angles=(0, 0))],
        symmetric=True,
        default_rule=PlyRule(removable=True),
    )
    with pytest.raises(InvalidDesign, match="minimum_plies"):
        space.decode([0])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0])
def test_nonpositive_or_nonfinite_thickness_rejected(value):
    with pytest.raises(ValueError):
        AnalysisPlyInfo.from_local_ply(id="p", material_name="A", angle=0, thickness=value)


def test_global_addition_gap_projects_into_local_stacks():
    first = laminate()
    second = replace(laminate("two"), plies=(first.plies[0], first.plies[3]))
    space = LaminateDesignSpace([first, second], additions=[AdditionRule("insert", ("A",), 0.5)])
    assert space.global_ply_ids == ("p0", "p1", "p2", "p3")
    points = space.decode(candidate(space, **{
        "added:insert:0.active": 1,
        "added:insert:0.position": 2,
    }))
    assert [p.id for p in points[0].plies] == ["p0", "p1", "added:insert:0", "p2", "p3"]
    assert [p.id for p in points[1].plies] == ["p0", "added:insert:0", "p3"]


def test_added_global_position_tracks_reordering_and_removal():
    point = laminate(angles=(0, 45, 45, 0))
    space = LaminateDesignSpace(
        [point], symmetric=True, allow_reordering=True,
        default_rule=PlyRule(removable=True),
        additions=[AdditionRule("new", ("A",), 0.5)],
    )
    decoded = space.decode(candidate(space, **{
        "p0.active": 0,
        "p0.order": 1,
        "p1.order": 0,
        "added:new:0.active": 1,
        "added:new:0.position": 1,
    }))[0]
    assert [p.id for p in decoded.plies] == [
        "p1", "added:new:0", "added:new:0:mirror", "p2",
    ]


def test_symmetric_addition_gaps_are_restricted_to_lower_half():
    space = LaminateDesignSpace(
        [laminate()], symmetric=True, additions=[AdditionRule("new", ("A",), 0.5)]
    )
    assert space._addition_positions["new"] == (0, 1, 2)
    with pytest.raises(ValueError, match="outside its bounds"):
        space.decode(candidate(space, **{"added:new:0.active": 1, "added:new:0.position": 3}))


def test_insertion_position_variable_is_an_integer_index():
    space = LaminateDesignSpace([laminate()], additions=[AdditionRule("new", ("A",), 1)])
    variable = next(v for v in space.variables if v.name == "added:new:0.position")
    assert variable.integer
    with pytest.raises(ValueError, match="integer index"):
        space.decode(candidate(space, **{"added:new:0.position": 0.5}))


def test_material_group_validation():
    with pytest.raises(ValueError, match="Unknown material"):
        LaminateDesignSpace([laminate()], default_rule=PlyRule(materials=("missing",)))
    with pytest.raises(ValueError, match="include each initial"):
        LaminateDesignSpace([laminate()], default_rule=PlyRule(materials=("B",)))


def test_inconsistent_input_units_and_point_identities_rejected():
    with pytest.raises(ValueError, match="unit system"):
        LaminateDesignSpace([laminate(), replace(laminate("two"), unit_system="US")])
    with pytest.raises(ValueError, match="identities"):
        LaminateChangeSet.between([laminate()], [])


def test_dpf_missing_operator_message(monkeypatch):
    from ansys.dpf.composites.optimization import _evaluator

    def missing(*args, **kwargs):
        raise KeyError("unknown operator")

    monkeypatch.setattr(_evaluator, "Operator", missing)
    evaluator = ClassicalLaminateEvaluator(SimpleNamespace(_server=None), in_plane_criterion())
    with pytest.raises(RuntimeError, match="CLT-capable"):
        evaluator(laminate(), laminate().load_cases[0])


def test_pyacp_addition_templates_and_explicit_order():
    point = laminate(angles=(0, 0))
    space = LaminateDesignSpace(
        [point],
        symmetric=True,
        additions=[AdditionRule("skin", ("A",), 1)],
        offset_policy="bottom",
    )
    problem = LaminateOptimizationProblem(
        space, evaluate, objective=lambda points, _: -points[0].thickness
    )
    result = problem.optimize(lambda _: {"x": [1, 0, 0, 0], "success": True})
    stored = []
    updates = []
    bindings = {"p0": acp_ply(), "p1": acp_ply()}
    source = bindings["p0"]
    source.parent = object()
    source.clone = lambda: SimpleNamespace(store=lambda parent: stored.append(parent))
    adapter = PyACPAdapter(
        SimpleNamespace(update=lambda: updates.append(True)),
        bindings,
        fabrics={"A": source.ply_material},
    )
    with pytest.raises(ValueError, match="global_order"):
        adapter.apply(result)
    order = {p.id: i for i, p in enumerate(result.best.laminates[0].plies)}
    with pytest.raises(ValueError, match="template"):
        adapter.apply(result, global_order=order)
    templates = {
        p.id: ACPAdditionTemplate(source)
        for p in result.best.laminates[0].plies
        if p.id.startswith("added:")
    }
    plan = adapter.apply(result, global_order=order, addition_templates=templates)
    assert sum(p.operation == "add" for p in plan) == 2
    assert not stored and not updates
    adapter.apply(result, dry_run=False, global_order=order, addition_templates=templates)
    assert len(stored) == 2 and len(updates) == 1
    assert set(adapter.bindings) == set(order)
    assert adapter.bindings["added:skin:0"].global_ply_nr == 0


def test_pyacp_material_substitution_needs_matching_fabric():
    space = LaminateDesignSpace(
        [laminate(angles=(0, 0))],
        symmetric=True,
        default_rule=PlyRule(materials=("A", "B")),
    )
    result = LaminateOptimizationProblem(space, evaluate).optimize(
        lambda _: {"x": [1], "success": True}
    )
    bindings = {"p0": acp_ply(), "p1": acp_ply()}
    model = SimpleNamespace(update=lambda: None)
    with pytest.raises(ValueError, match="fabric"):
        PyACPAdapter(model, bindings).apply(result)
    fabric = SimpleNamespace(material=object(), thickness=1)
    PyACPAdapter(model, bindings, fabrics={"B": fabric}).apply(result, dry_run=False)
    assert all(p.ply_material is fabric for p in bindings.values())


def test_pyacp_reordering_without_property_edits():
    point = laminate()
    space = LaminateDesignSpace([point], symmetric=True, allow_reordering=True)
    problem = LaminateOptimizationProblem(
        space, evaluate, objective=lambda points, _: 0 if points[0].plies[0].id == "p1" else 1
    )
    result = problem.optimize(lambda _: {"x": [1, 0], "success": True})
    assert not result.changes.changes
    bindings = {p.id: acp_ply(p.angle) for p in point.plies}
    adapter = PyACPAdapter(SimpleNamespace(update=lambda: None), bindings)
    with pytest.raises(ValueError, match="global_order"):
        adapter.apply(result)
    order = {p.id: i for i, p in enumerate(result.best.laminates[0].plies)}
    adapter.apply(result, global_order=order, dry_run=False)
    assert {key: ply.global_ply_nr for key, ply in bindings.items()} == order


def test_invalid_angle_domain_objects_are_rejected():
    with pytest.raises(TypeError, match="AngleBounds"):
        PlyRule(angles=[0, 45])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AngleBounds"):
        AdditionRule("new", ("A",), 1, angles=[0, 45])  # type: ignore[arg-type]


def test_spatial_extent_optimizer_prunes_only_feasible_connected_tail():
    points = tuple(
        replace(laminate(f"element-{element_id}", angles=(0, 0)), element_id=element_id)
        for element_id in range(1, 5)
    )
    design_space = LaminateDesignSpace(points, default_rule=PlyRule())
    neighbors = {1: (2,), 2: (1, 3), 3: (2, 4), 4: (3,)}
    extents = SpatialPlyExtentOptimizer(
        neighbors,
        element_weights={1: 1, 2: 2, 3: 3, 4: 4},
        minimum_plies=1,
    )
    assessed_masks = []

    def evaluator(point, case):
        present = {ply.id for ply in point.plies}
        assessed_masks.append((point.element_id, "p0" in present))
        # Every element requires p1; only element 1 requires p0.
        irf = (
            2.0
            if "p1" not in present or (point.element_id == 1 and "p0" not in present)
            else 0.1
        )
        return LaminateResponse(float(len(point.plies)), (irf,) * len(point.plies))

    problem = LaminateOptimizationProblem(
        design_space,
        evaluator,
        irf_limit=0.8,
        extent_optimizer=extents,
    )
    result = problem.evaluate([])
    p0_extent = {
        point.element_id for point in result.laminates if any(p.id == "p0" for p in point.plies)
    }
    assert result.max_violation == 0
    assert p0_extent == {1}
    assert all([p.id for p in point.plies] == (["p0", "p1"] if point.element_id == 1 else ["p1"])
               for point in result.laminates)
    assert result.extent_search_complete
    assert (2, "p0") in result.extent_removals
    assert result.extent_evaluations > 1
    # Every p0 mask assessed by the inner optimizer remains connected.
    for start in range(0, len(assessed_masks), 4):
        mask = {
            element_id
            for element_id, present in assessed_masks[start : start + 4]
            if present
        }
        if mask:
            reached = {min(mask)}
            frontier = list(reached)
            while frontier:
                for neighbor in neighbors[frontier.pop()] :
                    if neighbor in mask and neighbor not in reached:
                        reached.add(neighbor)
                        frontier.append(neighbor)
            assert reached == mask


def test_spatial_extent_respects_custom_constraints_and_budget():
    points = tuple(
        replace(laminate(f"element-{element_id}", angles=(0, 0)), element_id=element_id)
        for element_id in (1, 2, 3)
    )
    design_space = LaminateDesignSpace(points, default_rule=PlyRule())
    extents = SpatialPlyExtentOptimizer(
        {1: (2,), 2: (1, 3), 3: (2,)}, max_evaluations=1
    )
    calls = []

    def evaluator(point, case):
        calls.append(point.element_id)
        irf = 0.1 if len(point.plies) == 2 else 1.0
        return LaminateResponse(float(len(point.plies)), (irf,) * len(point.plies))

    problem = LaminateOptimizationProblem(
        design_space,
        evaluator,
        irf_limit=0.8,
        constraints=[lambda laminates, _: -1.0 if all(len(p.plies) == 2 for p in laminates) else 1.0],
        extent_optimizer=extents,
    )
    result = problem.evaluate([])
    assert result.max_violation == 0
    assert result.extent_search_complete is False
    assert result.extent_evaluations == 1
    assert all(len(point.plies) == 2 for point in result.laminates)


@pytest.mark.parametrize(
    "neighbors",
    [
        {},
        {1: (2,), 2: ()},
        {1: (1,)},
    ],
)
def test_spatial_extent_validates_connectivity_graph(neighbors):
    with pytest.raises(ValueError):
        SpatialPlyExtentOptimizer(neighbors)


def test_sampling_point_global_ply_numbers_are_not_local_indices():
    point = laminate()
    document = point.to_clt_dict(point.load_cases[0])
    numbers = [0, 17, 1234, 2**60 + 3]
    for ply, number in zip(document["layup"]["analysis_plies"], numbers):
        ply["global_ply_number"] = number
    copied = Laminate.from_sampling_point(document)
    exported = copied.to_clt_dict(copied.load_cases[0])
    assert [p["global_ply_number"] for p in exported["layup"]["analysis_plies"]] == numbers
    assert [p.global_ply_number for p in copied.plies] == numbers
    assert (
        json.loads(json.dumps(exported))["layup"]["analysis_plies"][-1]["global_ply_number"]
        == numbers[-1]
    )


def test_global_ply_numbers_survive_edits_removal_and_reordering():
    point = laminate()
    document = point.to_clt_dict(point.load_cases[0])
    source_numbers = {"p0": 10, "p1": 30, "p2": 70, "p3": 90}
    for ply in document["layup"]["analysis_plies"]:
        ply["global_ply_number"] = source_numbers[ply["id"]]
    point = Laminate.from_sampling_point(document)
    space = LaminateDesignSpace(
        [point],
        symmetric=True,
        allow_reordering=True,
        default_rule=PlyRule(DiscreteAngles((0, 45, 90)), materials=("A", "B"), removable=True),
    )
    reordered = space.decode(
        candidate(
            space,
            **{
                "p0.order": 1,
                "p1.order": 0,
                "p1.angle": 2,
                "p1.material": 1,
            },
        )
    )[0]
    exported = reordered.to_clt_dict(reordered.load_cases[0])["layup"]["analysis_plies"]
    assert [p["id"] for p in exported] == ["p1", "p0", "p3", "p2"]
    assert [p["global_ply_number"] for p in exported] == [30, 10, 90, 70]
    removed = space.decode(candidate(space, **{"p0.active": 0}))[0]
    assert [p.global_ply_number for p in removed.plies] == [30, 70]
    changes = LaminateChangeSet.between([point], [removed]).to_dict()
    assert changes["changes"][0]["before"]["global_ply_number"] == 10
    assert changes["optimized"][0]["plies"][0]["global_ply_number"] == 30


def test_added_global_ply_numbers_are_stable_and_shared():
    first = laminate()
    second = replace(laminate("two"), plies=(first.plies[0], first.plies[-1]))
    space = LaminateDesignSpace(
        [first, second],
        symmetric=True,
        additions=[AdditionRule("new", ("A",), 1, max_count=2)],
    )
    values = candidate(space, **{"added:new:0.active": 1, "added:new:1.active": 1})
    decoded = space.decode(values)
    first_numbers = {
        p.id: p.global_ply_number for p in decoded[0].plies if p.id.startswith("added:")
    }
    second_numbers = {
        p.id: p.global_ply_number for p in decoded[1].plies if p.id.startswith("added:")
    }
    assert first_numbers == second_numbers
    assert len(set(first_numbers.values())) == 4
    original_numbers = {p.global_ply_number for p in first.plies}
    assert not original_numbers.intersection(first_numbers.values())
    assert all(number is not None for number in first_numbers.values())
    partial = space.decode(candidate(space, **{"added:new:1.active": 1}))[0]
    assert {p.id: p.global_ply_number for p in partial.plies if p.id.startswith("added:")} == {
        key: number for key, number in first_numbers.items() if key.startswith("added:new:1")
    }


@pytest.mark.parametrize("number", [-1, True, 1.5, "12"])
def test_invalid_global_ply_number_rejected(number):
    with pytest.raises(ValueError, match="global_ply_number"):
        AnalysisPlyInfo.from_local_ply(
            id="p", material_name="A", angle=0, thickness=1,
            global_ply_number=number,
        )


def test_export_missing_ply_numbers_does_not_collide_with_preserved_numbers():
    point = laminate(angles=(0, 0))
    point = replace(
        point,
        plies=(
            replace(point.plies[0], global_ply_number=2),
            replace(point.plies[1], global_ply_number=None),
        ),
    )
    exported = point.to_clt_dict(point.load_cases[0])["layup"]["analysis_plies"]
    assert exported[0]["global_ply_number"] == 2
    assert exported[1]["global_ply_number"] != 2


def test_conflicting_shared_global_ply_numbers_rejected():
    first = laminate()
    second = replace(
        laminate("two"),
        plies=(
            replace(first.plies[0], global_ply_number=100),
            *first.plies[1:],
        ),
    )
    with pytest.raises(ValueError, match="global_ply_number"):
        LaminateDesignSpace([first, second])
