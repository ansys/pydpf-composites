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

from ansys.dpf.composites.failure_criteria._core_failure import (
    ATTRS_CORE_FAILURE,
    CoreFailureCriterion,
)

defaults = dict(zip(ATTRS_CORE_FAILURE, [False, 1.0]))


def test_core_failure_criterion():
    cf_default = CoreFailureCriterion()
    assert cf_default.name == "Core Failure"

    defaults_dict = {"active": True}
    for v in ATTRS_CORE_FAILURE:
        assert getattr(cf_default, v) == defaults[v]
        defaults_dict[v] = defaults[v]

    attr_values = cf_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

    json_dumps = '{"active": true, "include_ins": false, "wf": 1.0}'

    assert json_dumps == cf_default.to_json()

    new_values = dict(zip(ATTRS_CORE_FAILURE, [True, 2.0]))

    cf = CoreFailureCriterion(**new_values)
    for v in ATTRS_CORE_FAILURE:
        assert getattr(cf, v) == new_values[v]

    # test setters
    for k, v in new_values.items():
        setattr(cf_default, k, v)
        assert getattr(cf_default, k) == v

    # test repr
    cf.__repr__()
