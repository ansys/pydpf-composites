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

from ansys.dpf.composites.failure_criteria._larc import ATTRS_LARC, LaRCCriterion

defaults = dict(zip(ATTRS_LARC, [True, True, True, True, 2, 1.0, 1.0, 1.0, 1.0]))


def test_larc_criterion():
    larc_default = LaRCCriterion()
    assert larc_default.name == "LaRC"

    defaults_dict = {"active": True}
    for key in ATTRS_LARC:
        value = getattr(larc_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = larc_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "dim": 2, "lfc": true, "lft": true, "lmc": true, "lmt": true, '
        '"wf_lfc": 1.0, "wf_lft": 1.0, "wf_lmc": 1.0, "wf_lmt": 1.0}'
    )

    assert json_dumps == larc_default.to_json()

    new_values = dict(zip(ATTRS_LARC, [False, False, False, False, 3, 2.0, 4.0, 5.0, 6.0]))

    larc = LaRCCriterion(**new_values)
    for key in ATTRS_LARC:
        value = getattr(larc, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(larc_default, k, v)
        assert getattr(larc_default, k) == v

    # test repr
    larc.__repr__()
