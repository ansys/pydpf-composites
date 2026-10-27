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

"""Optional SciPy solver callables; importing optimization does not import SciPy."""

from typing import Any

from ._problem import LaminateOptimizationProblem


def scipy_differential_evolution(problem: LaminateOptimizationProblem, **options: Any) -> Any:
    """Mixed-variable search using exact integer categorical indices.

    Execution is serial because DPF operators/servers are not multiprocessing
    payloads. Supply a different driver with isolated evaluators for parallel
    optimization. SciPy >= 1.9 is required.
    """
    from scipy.optimize import NonlinearConstraint, differential_evolution

    protected = {"func", "bounds", "constraints", "x0", "integrality", "workers", "vectorized"}
    if options.keys() & protected:
        raise ValueError(
            f"Driver-managed options cannot be overridden: {options.keys() & protected}"
        )
    return differential_evolution(
        problem.objective,
        problem.design_space.bounds,
        constraints=NonlinearConstraint(problem.constraint_values, -float("inf"), 0),
        x0=problem.design_space.initial,
        integrality=problem.design_space.integrality,
        workers=1,
        **options,
    )


def scipy_minimize(problem: LaminateOptimizationProblem, **options: Any) -> Any:
    """Continuous constrained search, defaulting to SLSQP.

    Discrete choices, existence variables, and permutation keys are rejected.
    Use differential evolution or a custom mixed-variable driver instead.
    """
    from scipy.optimize import minimize

    if any(v.integer or v.name.endswith(".order") for v in problem.design_space.variables):
        raise ValueError("scipy_minimize requires continuous, fixed-topology variables.")
    protected = {"fun", "x0", "bounds", "constraints"}
    if options.keys() & protected:
        raise ValueError(
            f"Driver-managed options cannot be overridden: {options.keys() & protected}"
        )
    method = options.pop("method", "SLSQP")
    if method not in ("SLSQP", "COBYLA", "COBYQA", "trust-constr"):
        raise ValueError("Choose a SciPy method that supports nonlinear inequality constraints.")
    return minimize(
        problem.objective,
        problem.design_space.initial,
        method=method,
        bounds=problem.design_space.bounds,
        constraints={"type": "ineq", "fun": lambda x: [-v for v in problem.constraint_values(x)]},
        **options,
    )
