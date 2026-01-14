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

from ansys.dpf.composites.failure_criteria._combined_failure_criterion import (
    CombinedFailureCriterion,
)
from ansys.dpf.composites.failure_criteria._max_strain import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria._max_stress import MaxStressCriterion


def test_combined_failure_criterion():
    cfc = CombinedFailureCriterion("my name")
    assert cfc.name == "my name"

    cfc.failure_criteria
    assert len(cfc.failure_criteria) == 0

    strain = MaxStrainCriterion()
    stress = MaxStressCriterion()
    cfc.insert(strain)
    cfc.insert(stress)

    assert len(cfc.failure_criteria) == 2

    removed = cfc.remove(strain.name)
    assert removed.name == "Max Strain"
    assert len(cfc.failure_criteria) == 1
    cfc.insert(stress)
    # still 1 FC because max stress was already added. Old entry is replaced
    assert len(cfc.failure_criteria) == 1
    cfc.insert(strain)

    attrs_d = cfc.to_dict()
    assert "max_stress" in attrs_d.keys()
    assert "max_strain" in attrs_d.keys()

    ref_d = {
        "max_stress": {
            "active": True,
            "s12": True,
            "s13": False,
            "s1": True,
            "s23": False,
            "s2": True,
            "s3": False,
            "wf_s1": 1.0,
            "wf_s12": 1.0,
            "wf_s13": 1.0,
            "wf_s2": 1.0,
            "wf_s23": 1.0,
            "wf_s3": 1.0,
        },
        "max_strain": {
            "active": True,
            "eSxy": 0.0,
            "e12": True,
            "eSxz": 0.0,
            "e13": False,
            "e1": True,
            "eXc": 0.0,
            "eXt": 0.0,
            "eSyz": 0.0,
            "e23": False,
            "e2": True,
            "eYc": 0.0,
            "eYt": 0.0,
            "e3": False,
            "eZc": 0.0,
            "eZt": 0.0,
            "force_global_strain_limits": False,
            "wf_e1": 1.0,
            "wf_e12": 1.0,
            "wf_e13": 1.0,
            "wf_e2": 1.0,
            "wf_e23": 1.0,
            "wf_e3": 1.0,
        },
    }

    assert attrs_d == ref_d

    # test repr
    cfc.__repr__()
