# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    CuntzeCriterion,
    HashinCriterion,
    HoffmanCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    TsaiHillCriterion,
    TsaiWuCriterion,
    VonMisesCriterion,
)


def get_basic_combined_failure_criterion():
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    tsai_hill = TsaiHillCriterion()
    tsai_wu = TsaiWuCriterion()
    hoffman = HoffmanCriterion()
    hashin = HashinCriterion()
    cuntze = CuntzeCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)

    cfc = CombinedFailureCriterion()
    cfc.insert(max_strain)
    cfc.insert(max_stress)
    cfc.insert(tsai_hill)
    cfc.insert(tsai_wu)
    cfc.insert(hoffman)
    cfc.insert(hashin)
    cfc.insert(cuntze)
    cfc.insert(core_failure)
    cfc.insert(von_mises_strain_only)
    return cfc
