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

from ansys.dpf.composites.failure_criteria._puck import ATTRS_PUCK, PuckCriterion

defaults = dict(
    zip(
        ATTRS_PUCK,
        [
            True,
            True,
            True,
            True,
            False,
            2,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            True,
            0.5,
            0.5,
            0.8,
            False,
            0.275,
            0.325,
            0.225,
            0.225,
        ],
    )
)


def test_puck_criterion():
    puck_default = PuckCriterion()
    assert puck_default.name == "Puck"

    defaults_dict = {"active": True}
    for key in ATTRS_PUCK:
        value = getattr(puck_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = puck_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"M": 0.5, "active": true, "cfps": true, "dim": 2, '
        '"force_global_constants": false, "interface_weakening_factor": 0.8, "p21_neg": 0.275, '
        '"p21_pos": 0.325, "p22_neg": 0.225, "p22_pos": 0.225, "pd": false, "pf": true, '
        '"pma": true, "pmb": true, "pmc": true, "s": 0.5, "wf_pd": 1.0, "wf_pf": 1.0, '
        '"wf_pma": 1.0, "wf_pmb": 1.0, "wf_pmc": 1.0}'
    )

    assert json_dumps == puck_default.to_json()

    new_values = dict(
        zip(
            ATTRS_PUCK,
            [
                False,
                False,
                False,
                False,
                True,
                3,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                False,
                0.75,
                0.8,
                0.9,
                True,
                0.28,
                0.31,
                0.24,
                0.23,
            ],
        )
    )

    puck = PuckCriterion(**new_values)
    for key in ATTRS_PUCK:
        value = getattr(puck, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(puck_default, k, v)
        assert getattr(puck_default, k) == v

    # test repr
    puck.__repr__()
