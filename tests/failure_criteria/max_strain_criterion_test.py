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

from ansys.dpf.composites.failure_criteria._max_strain import ATTRS_MAX_STRAIN, MaxStrainCriterion

defaults = dict(
    zip(
        ATTRS_MAX_STRAIN,
        [
            True,
            True,
            False,
            True,
            False,
            False,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            False,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    )
)


def test_max_strain_criterion():
    ms_default = MaxStrainCriterion()
    assert ms_default.name == "Max Strain"

    defaults_dict = {"active": True}
    for key in ATTRS_MAX_STRAIN:
        assert getattr(ms_default, key) == defaults[key]
        defaults_dict[key] = defaults[key]

    attr_values = ms_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

    json_dumps = (
        '{"active": true, "e1": true, "e12": true, "e13": false, "e2": true, "e23": false, '
        '"e3": false, "eSxy": 0.0, "eSxz": 0.0, "eSyz": 0.0, "eXc": 0.0, "eXt": 0.0, "eYc": 0.0, '
        '"eYt": 0.0, "eZc": 0.0, "eZt": 0.0, "force_global_strain_limits": false, '
        '"wf_e1": 1.0, "wf_e12": 1.0, "wf_e13": 1.0, "wf_e2": 1.0, "wf_e23": 1.0, "wf_e3": 1.0}'
    )

    assert json_dumps == ms_default.to_json()

    new_values = dict(
        zip(
            ATTRS_MAX_STRAIN,
            [
                False,
                False,
                True,
                False,
                True,
                True,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                True,
                0.01,
                -0.1,
                0.02,
                -0.2,
                0.03,
                -0.3,
                0.15,
                0.25,
                0.35,
            ],
        )
    )

    ms = MaxStrainCriterion(**new_values)
    for v in ATTRS_MAX_STRAIN:
        assert getattr(ms, v) == new_values[v]

    # test setters
    for k, v in new_values.items():
        setattr(ms_default, k, v)
        assert getattr(ms_default, k) == v

    # test repr
    ms.__repr__()
