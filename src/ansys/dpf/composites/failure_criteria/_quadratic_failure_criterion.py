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

"""Base class for quadratic failure criterion."""

from ._failure_criterion_base import FailureCriterionBase

_DOC_WF = "Weighting factor of this failure criterion."
_DOC_DIM = "Specifies which formulation of the failure criterion is used."


class QuadraticFailureCriterion(FailureCriterionBase):
    """Base class for quadratic failure criteria.

    Such as Tsai-Wu, Tsai-Hill and Hoffman.
    """

    def __init__(self, *, name: str, active: bool, wf: float, dim: int):
        """Do not use directly. Base class for quadratic failure criteria."""
        super().__init__(name=name, active=active)

        self.dim = dim
        self.wf = wf

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3."
            )

    wf = property(_get_wf, _set_wf, doc=_DOC_WF)
    dim = property(_get_dim, _set_dim, doc=_DOC_DIM)
