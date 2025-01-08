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

"""Module of failure criteria."""

from ._combined_failure_criterion import CombinedFailureCriterion
from ._core_failure import CoreFailureCriterion
from ._cuntze import CuntzeCriterion
from ._face_sheet_wrinkling import FaceSheetWrinklingCriterion
from ._failure_mode_enum import FailureModeEnum
from ._hashin import HashinCriterion
from ._hoffman import HoffmanCriterion
from ._larc import LaRCCriterion
from ._max_strain import MaxStrainCriterion
from ._max_stress import MaxStressCriterion
from ._puck import PuckCriterion
from ._shear_crimping import ShearCrimpingCriterion
from ._tsai_hill import TsaiHillCriterion
from ._tsai_wu import TsaiWuCriterion
from ._von_mises import VonMisesCriterion

__all__ = [
    "MaxStrainCriterion",
    "MaxStressCriterion",
    "CombinedFailureCriterion",
    "TsaiWuCriterion",
    "TsaiHillCriterion",
    "HoffmanCriterion",
    "CoreFailureCriterion",
    "CuntzeCriterion",
    "FaceSheetWrinklingCriterion",
    "HashinCriterion",
    "LaRCCriterion",
    "PuckCriterion",
    "ShearCrimpingCriterion",
    "VonMisesCriterion",
    "FailureModeEnum",
]
