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

import pytest

from ansys.dpf.composites.failure_criteria._cuntze import ATTRS_CUNTZE, CuntzeCriterion

defaults = dict(
    zip(
        ATTRS_CUNTZE,
        [True, True, True, True, True, 2, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 1.3805, 53.0, 2.6],
    )
)


def test_cuntze_criterion():
    cuntze_default = CuntzeCriterion()
    assert cuntze_default.name == "Cuntze"

    defaults_dict = {"active": True}
    for key in ATTRS_CUNTZE:
        value = getattr(cuntze_default, key)
        if key in ["b32", "fracture_plane_angle"]:
            assert abs(value - defaults[key]) < 1.0e-4, f"{key}: {value} != {defaults[key]}"
        else:
            assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = cuntze_default.to_dict()
    for key, value in attr_values.items():
        if key in ["b32", "fracture_plane_angle"]:
            assert abs(value - defaults[key]) < 1.0e-4, f"{key}: {value} != {defaults[key]}"
        else:
            assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "b21": 0.2, "b32": 1.3805239792947728, "cfc": true, '
        '"cft": true, "cma": true, "cmb": true, "cmc": true, "dim": 2, '
        '"fracture_plane_angle": 53.0, "mode_interaction_coeff": 2.6, '
        '"wf_cfc": 1.0, "wf_cft": 1.0, "wf_cma": 1.0, "wf_cmb": 1.0, "wf_cmc": 1.0}'
    )

    assert json_dumps == cuntze_default.to_json()

    new_values = dict(
        zip(
            ATTRS_CUNTZE,
            [False, False, False, False, False, 3, 2.0, 4.0, 5.0, 6.0, 7.0, 0.4, 2.0, 60.0, 3.0],
        )
    )

    cuntze = CuntzeCriterion(**new_values)
    for key in ATTRS_CUNTZE:
        value = getattr(cuntze, key)
        if key in ["b32", "fracture_plane_angle"]:
            assert value == pytest.approx(new_values[key]), f"{key}: {value} != {new_values[key]}"
        else:
            assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(cuntze_default, k, v)
        assert getattr(cuntze_default, k) == v

    # test repr
    cuntze.__repr__()
