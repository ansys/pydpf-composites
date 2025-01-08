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

"""Core failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_INCLUDE_INS = (
    "Whether to activate the formulation that considers interlaminar normal stresses."
)

_DOC_WF = "Weighting factor of the failure mode (cs)."


class CoreFailureCriterion(FailureCriterionBase):
    """Defines the core failure criterion."""

    __doc__ = f"""Defines the core shear failure criterion for
    core materials like foam and honeycomb.

    Parameters
    ----------
    include_ins:
        {_DOC_INCLUDE_INS}
    wf:
        {_DOC_WF}
    """

    def __init__(self, *, include_ins: bool = False, wf: float = 1.0):
        """Create a core failure criterion."""
        super().__init__(name="Core Failure", active=True)

        for attr in ATTRS_CORE_FAILURE:
            setattr(self, attr, eval(attr))

    def _get_include_ins(self) -> bool:
        return self._include_ins

    def _set_include_ins(self, value: bool) -> None:
        self._include_ins = value

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    include_ins = property(_get_include_ins, _set_include_ins, doc=_DOC_INCLUDE_INS)
    wf = property(_get_wf, _set_wf, doc=_DOC_WF)


ATTRS_CORE_FAILURE = inspect.signature(CoreFailureCriterion).parameters.keys()
