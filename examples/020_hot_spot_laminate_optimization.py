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

"""
.. _hot_spot_laminate_optimization_example:

Hot spot laminate optimization
------------------------------

This example performs a 2D maximum-stress sampling-point analysis for element
2999 and runs three fixed-resultant CLT optimizations:

1. Optimize ply angles from 0 to 90 degrees in 15-degree increments.
2. Optimize those angles and replace materials between the supplied UD and
   woven materials.
3. Optimize the full sampled stack: angles and materials, bounded additions,
   and a connectivity-constrained local removal mask.

The input files are read from ``D:/tmp/acp_optimization`` by default. Override
that directory with ``DPF_COMPOSITES_OPTIMIZATION_INPUT``. The DPF Composites
plugin must provide the standalone CLT operator and sampling-point JSON must
include material definitions and laminate resultants. The supplied RST is
already solved; this example does not run MAPDL again.

The third optimization only has one sample element, so its local graph contains
one node. For a region of elements, provide the real edge-sharing element graph
to ``SpatialPlyExtentOptimizer`` to enforce continuous extents and avoid
checkerboard islands.
"""

# %%
# Imports and input files
# ~~~~~~~~~~~~~~~~~~~~~~
import os
from pathlib import Path
from typing import Any

from ansys.dpf import core as dpf
from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.optimization import (
    AdditionRule,
    ClassicalLaminateEvaluator,
    DiscreteAngles,
    Laminate,
    LaminateDesignSpace,
    LaminateOptimizationProblem,
    PlyRule,
    SpatialPlyExtentOptimizer,
    scipy_differential_evolution,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

INPUT_DIRECTORY = Path(
    os.environ.get("DPF_COMPOSITES_OPTIMIZATION_INPUT", r"D:\tmp\acp_optimization")
)
ELEMENT_ID = 2999
IRF_LIMIT = 0.8
ALLOWED_ANGLES = DiscreteAngles((0, 15, 30, 45, 60, 75, 90))
ALLOWED_MATERIALS = (
    "Epoxy_Carbon_UD",
    "Epoxy_Carbon_Woven_230GPa_Prepreg",
)

# Small settings keep this example demonstrative. Increase maxiter, popsize,
# and max_extent_evaluations for an engineering search; each objective call
# runs the DPF CLT operator (and the full-stack case also tries local removals).
DE_OPTIONS = {"seed": 42, "maxiter": 20, "popsize": 50, "polish": False}
MAX_EXTENT_EVALUATIONS = 20
ANSYS_PATH = os.environ.get("DPF_COMPOSITES_ANSYS_PATH")


def main() -> None:
    """Analyze element 2999, then run the three requested CLT searches."""
    required_files = (
        INPUT_DIRECTORY / "file.rst",
        INPUT_DIRECTORY / "ACPCompositeDefinitions.h5",
        INPUT_DIRECTORY / "materials.xml",
    )
    missing_files = [path for path in required_files if not path.is_file()]
    if missing_files:
        print(
            "Skipping hot-spot laminate optimization; input files were not found: "
            + ", ".join(str(path) for path in missing_files)
            + ". Set DPF_COMPOSITES_OPTIMIZATION_INPUT to the input directory."
        )
        return

    # %%
    # Start DPF and analyze the hot-spot sampling point
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    server = connect_to_or_start_server(ansys_path=ANSYS_PATH)
    composite_files = ContinuousFiberCompositesFiles(
        result_files=INPUT_DIRECTORY / "file.rst",
        composite={
            "shell": CompositeDefinitionFiles(
                definition=INPUT_DIRECTORY / "ACPCompositeDefinitions.h5"
            )
        },
        engineering_data=INPUT_DIRECTORY / "materials.xml",
    )
    composite_model = CompositeModel(composite_files, server=server)

    max_stress_2d = CombinedFailureCriterion(
        name="2D maximum stress",
        failure_criteria=[
            MaxStressCriterion(s1=True, s2=True, s3=False, s12=True, s13=False, s23=False)
        ],
    )
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=max_stress_2d,
        element_id=ELEMENT_ID,
    )
    print(f"Element {ELEMENT_ID} analysis plies:")
    for analysis_ply in sampling_point.analysis_plies:
        print(
            f"  {analysis_ply['id']}: angle={analysis_ply['angle']} deg, "
            f"material={analysis_ply['material']}, "
            f"thickness={analysis_ply['thickness']}"
        )
    print(
        "Maximum sampling-point IRF:",
        max(sampling_point.results[0]["results"]["failures"]["inverse_reserve_factor"]),
    )

    # Check capabilities after running the requested sampling-point analysis.
    # Older plugins can evaluate a sampling point but lack standalone CLT and
    # its material/force input data.
    try:
        dpf.Operator("composite::classical_laminate_theory_operator", server=server)
    except KeyError as error:
        raise RuntimeError(
            "This example's optimization phase requires a DPF Composites plugin build "
            "that provides composite::classical_laminate_theory_operator."
        ) from error

    sample_document = sampling_point.results[0]
    if "materials" not in sample_document:
        raise RuntimeError(
            "The sampling-point JSON does not export CLT material definitions. "
            "Use a CLT-capable DPF Composites plugin build."
        )
    try:
        initial_laminate = Laminate.from_sampling_point(
            sampling_point,
            name=f"hot_spot_{ELEMENT_ID}",
        )
    except ValueError as error:
        raise RuntimeError(
            "The sampling point must export laminate forces and material definitions "
            "for fixed-resultant CLT optimization."
        ) from error

    missing_materials = set(ALLOWED_MATERIALS) - {
        material.name for material in initial_laminate.materials
    }
    if missing_materials:
        raise ValueError(
            f"Requested material alternatives are not in the model: {missing_materials}"
        )

    clt_evaluator = ClassicalLaminateEvaluator(
        composite_model.material_operators.material_provider,
        max_stress_2d,
    )

    def run_optimization(
        title: str,
        *,
        ply_rule: PlyRule,
        additions: tuple[AdditionRule, ...] = (),
        extent_optimizer: SpatialPlyExtentOptimizer | None = None,
    ) -> Any:
        """Run one mass-minimization problem and print its feasibility/results."""
        design_space = LaminateDesignSpace(
            (initial_laminate,),
            default_rule=ply_rule,
            additions=additions,
            minimum_plies=1,
        )
        problem = LaminateOptimizationProblem(
            design_space,
            clt_evaluator,
            irf_limit=IRF_LIMIT,
            extent_optimizer=extent_optimizer,
        )
        result = problem.optimize(scipy_differential_evolution, **DE_OPTIONS)
        print(f"\n{title}")
        print(f"  feasible (IRF <= {IRF_LIMIT}): {result.feasible}")
        print(f"  solver status: {result.message}")
        print(f"  mass / area: {result.initial.objective:.6g} -> {result.best.objective:.6g}")
        print(
            f"  maximum IRF: {result.initial.results[0].response.max_irf:.6g} -> "
            f"{result.best.results[0].response.max_irf:.6g}"
        )
        print(f"  final ply count: {len(result.best.laminates[0].plies)}")
        print(f"  extent removals: {result.best.extent_removals}")
        return result

    # %%
    # 1. Optimize angles only
    # ~~~~~~~~~~~~~~~~~~~~~~~
    optimization_results = {}
    # Hold a single ACP PrepPost license increment for all candidate CLT
    # evaluations. The evaluator creates an operator for every candidate, but
    # the context manager prevents a checkout/check-in cycle on each evaluation.
    with dpf.LicenseContextManager(increment_name="acpreppost", server=server):
        optimization_results["angles_only"] = run_optimization(
            "Ply-angle optimization", ply_rule=PlyRule(angles=ALLOWED_ANGLES)
        )

        # %%
        # 2. Optimize angles and the UD/woven material choice
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        optimization_results["angles_and_materials"] = run_optimization(
            "Ply-angle and material optimization",
            ply_rule=PlyRule(angles=ALLOWED_ANGLES, materials=ALLOWED_MATERIALS),
        )

        # %%
        # 3. Optimize the complete stacking at the hot spot
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Use one addition rule per material so each product retains its own
        # measured thickness. Optional plies may use any optimizer-chosen gap.
        thickness_by_material = {
            material_name: next(
                ply.thickness
                for ply in initial_laminate.plies
                if ply.material_name == material_name
            )
            for material_name in ALLOWED_MATERIALS
        }
        full_stack_extent_optimizer = SpatialPlyExtentOptimizer(
            {ELEMENT_ID: ()},
            minimum_plies=1,
            max_evaluations=MAX_EXTENT_EVALUATIONS,
        )
        optimization_results["full_stacking"] = run_optimization(
            "Full stacking optimization",
            ply_rule=PlyRule(
                angles=ALLOWED_ANGLES,
                materials=ALLOWED_MATERIALS,
                removable=True,
            ),
            additions=(
                AdditionRule(
                    name="added_ud",
                    materials=("Epoxy_Carbon_UD",),
                    thickness=thickness_by_material["Epoxy_Carbon_UD"],
                    angles=ALLOWED_ANGLES,
                    max_count=1,
                ),
                AdditionRule(
                    name="added_woven",
                    materials=("Epoxy_Carbon_Woven_230GPa_Prepreg",),
                    thickness=thickness_by_material["Epoxy_Carbon_Woven_230GPa_Prepreg"],
                    angles=ALLOWED_ANGLES,
                    max_count=1,
                ),
            ),
            extent_optimizer=full_stack_extent_optimizer,
        )


if __name__ == "__main__":
    main()

