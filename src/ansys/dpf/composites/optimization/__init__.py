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

"""Fixed-resultant classical laminate optimization with optional mirror symmetry.

Use independent local CLT evaluations to screen designs. Changes in global
displacements, load redistribution, buckling and out-of-plane failures require
subsequent FE verification. No ACP model is changed during optimization.
"""

from ._design_space import (
    AdditionRule,
    AngleBounds,
    DesignVariable,
    DiscreteAngles,
    InvalidDesign,
    LaminateDesignSpace,
    PlyRule,
)
from ._evaluator import ClassicalLaminateEvaluator, LaminateEvaluator
from ._models import Laminate, LaminateForces, LaminateResponse, LoadCase, Material, Ply
from ._problem import (
    CandidateEvaluation,
    LaminateChangeSet,
    LaminateOptimizationProblem,
    LaminateOptimizationResult,
    PlyChange,
    PointResult,
)
from ._pyacp import ACPAdditionTemplate, ACPChange, PyACPAdapter
from ._scipy import scipy_differential_evolution, scipy_minimize
from ._spatial import SpatialPlyExtentOptimizer

__all__ = (
    "ACPAdditionTemplate",
    "ACPChange",
    "PyACPAdapter",
    "AdditionRule",
    "AngleBounds",
    "CandidateEvaluation",
    "ClassicalLaminateEvaluator",
    "DesignVariable",
    "DiscreteAngles",
    "InvalidDesign",
    "Laminate",
    "LaminateChangeSet",
    "LaminateDesignSpace",
    "LaminateEvaluator",
    "LaminateForces",
    "LaminateOptimizationProblem",
    "LaminateOptimizationResult",
    "LaminateResponse",
    "LoadCase",
    "Material",
    "Ply",
    "PlyChange",
    "PlyRule",
    "PointResult",
    "SpatialPlyExtentOptimizer",
    "scipy_differential_evolution",
    "scipy_minimize",
)
