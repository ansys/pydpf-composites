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

"""Face Sheet Wrinkling Criterion for sandwich structures."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_HOMOGENEOUS_CORE_COEFF = (
    "Wrinkling coefficient (reduction factor) for homogeneous core materials."
)
_DOC_HONEYCOMB_CORE_COEFF = (
    "Wrinkling coefficient (reduction factor) for honeycombs. The default is ``0.33``."
)
_DOC_WF = "Weighting factor of the failure mode (wb or wt). The default is ``0.5``."


class FaceSheetWrinklingCriterion(FailureCriterionBase):
    """Face Sheet Wrinkling Criterion."""

    __doc__ = f"""Defines the face sheet wrinkling criterion for sandwiches (laminate with cores).

    Parameters
    ----------
    homogeneous_core_coeff:
        {_DOC_HOMOGENEOUS_CORE_COEFF}
    honeycomb_core_coeff:
        {_DOC_HONEYCOMB_CORE_COEFF}
    wf:
        {_DOC_WF}
    """

    def __init__(
        self,
        *,
        homogeneous_core_coeff: float = 0.5,
        honeycomb_core_coeff: float = 0.33,
        wf: float = 1.0,
    ):
        """Construct a Face Sheet Wrinkling failure criterion."""
        super().__init__(name="Face Sheet Wrinkling", active=True)

        for attr in ATTRS_WRINKLING:
            setattr(self, attr, eval(attr))

    def _get_homogeneous_core_coeff(self) -> float:
        return self._homogeneous_core_coeff

    def _set_homogeneous_core_coeff(self, value: float) -> None:
        if value > 0:
            self._homogeneous_core_coeff = value
        else:
            raise ValueError("Homogeneous core coefficient must be greater than 0.")

    def _get_honeycomb_core_coeff(self) -> float:
        return self._honeycomb_core_coeff

    def _set_honeycomb_core_coeff(self, value: float) -> None:
        if value > 0:
            self._honeycomb_core_coeff = value
        else:
            raise ValueError("Honeycomb core coefficient must be greater than 0.")

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    homogeneous_core_coeff = property(
        _get_homogeneous_core_coeff,
        _set_homogeneous_core_coeff,
        doc=_DOC_HOMOGENEOUS_CORE_COEFF,
    )
    honeycomb_core_coeff = property(
        _get_honeycomb_core_coeff,
        _set_honeycomb_core_coeff,
        doc=_DOC_HONEYCOMB_CORE_COEFF,
    )

    wf = property(_get_wf, _set_wf, doc=_DOC_WF)


ATTRS_WRINKLING = inspect.signature(FaceSheetWrinklingCriterion).parameters.keys()
