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

"""Defines the MaxStress failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_S1 = (
    "Whether to activate the failure evaluation regarding the stress in the material 1 direction."
)
_DOC_S2 = (
    "Whether to activate the failure evaluation regarding the stress in the material 2 direction."
)
_DOC_S3 = (
    "Whether to activate the failure evaluation regarding the stress in the material "
    "3 direction (out-of-plane)."
)
_DOC_S12 = "Whether to activate the failure evaluation regarding the in-plane shear stress s12."
_DOC_S13 = "Whether to activate the failure evaluation regarding the interlaminar shear stress s13."
_DOC_S23 = "Whether to activate the failure evaluation regarding the interlaminar shear stress s23."
_DOC_WF_S1 = "Weighting factor of the failure mode s1."
_DOC_WF_S2 = "Weighting factor of the failure mode s2."
_DOC_WF_S3 = "Weighting factor of the failure mode s3."
_DOC_WF_S12 = "Weighting factor of the failure mode s12."
_DOC_WF_S13 = "Weighting factor of the failure mode s13."
_DOC_WF_S23 = "Weighting factor of the failure mode s23."


class MaxStressCriterion(FailureCriterionBase):
    """Max Stress Criterion."""

    __doc__ = f"""Defines the maximum stress failure criterion for orthotropic reinforced materials.

    Parameters
    ----------
    s1:
        {_DOC_S1}
    s2:
        {_DOC_S2}
    s3:
        {_DOC_S3}
    s12:
        {_DOC_S12}
    s13:
        {_DOC_S13}
    s23:
        {_DOC_S23}
    wf_s1:
        {_DOC_WF_S1}
    wf_s2:
        {_DOC_WF_S2}
    wf_s3:
        {_DOC_WF_S3}
    wf_s12:
        {_DOC_WF_S12}
    wf_s13:
        {_DOC_WF_S13}
    wf_s23:
        {_DOC_WF_S23}
    """

    def __init__(
        self,
        *,
        s1: bool = True,
        s2: bool = True,
        s3: bool = False,
        s12: bool = True,
        s13: bool = False,
        s23: bool = False,
        wf_s1: float = 1.0,
        wf_s2: float = 1.0,
        wf_s3: float = 1.0,
        wf_s12: float = 1.0,
        wf_s13: float = 1.0,
        wf_s23: float = 1.0,
    ):
        """Create a maximum stress failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Max Stress", active=True)

        for attr in ATTRS_MAX_STRESS:
            setattr(self, attr, eval(attr))

    def _get_s1(self) -> bool:
        return self._s1

    def _set_s1(self, value: bool) -> None:
        self._s1 = value

    def _get_s2(self) -> bool:
        return self._s2

    def _set_s2(self, value: bool) -> None:
        self._s2 = value

    def _get_s3(self) -> bool:
        return self._s3

    def _set_s3(self, value: bool) -> None:
        self._s3 = value

    def _get_s12(self) -> bool:
        return self._s12

    def _set_s12(self, value: bool) -> None:
        self._s12 = value

    def _get_s13(self) -> bool:
        return self._s13

    def _set_s13(self, value: bool) -> None:
        self._s13 = value

    def _get_s23(self) -> bool:
        return self._s23

    def _set_s23(self, value: bool) -> None:
        self._s23 = value

    def _get_wf_s1(self) -> float:
        return self._wf_s1

    def _set_wf_s1(self, value: float) -> None:
        self._wf_s1 = value

    def _get_wf_s2(self) -> float:
        return self._wf_s2

    def _set_wf_s2(self, value: float) -> None:
        self._wf_s2 = value

    def _get_wf_s3(self) -> float:
        return self._wf_s3

    def _set_wf_s3(self, value: float) -> None:
        self._wf_s3 = value

    def _get_wf_s12(self) -> float:
        return self._wf_s12

    def _set_wf_s12(self, value: float) -> None:
        self._wf_s12 = value

    def _get_wf_s13(self) -> float:
        return self._wf_s13

    def _set_wf_s13(self, value: float) -> None:
        self._wf_s13 = value

    def _get_wf_s23(self) -> float:
        return self._wf_s23

    def _set_wf_s23(self, value: float) -> None:
        self._wf_s23 = value

    s1 = property(_get_s1, _set_s1, doc=_DOC_S1)

    s2 = property(_get_s2, _set_s2, doc=_DOC_S2)

    s3 = property(_get_s3, _set_s3, doc=_DOC_S3)
    s12 = property(_get_s12, _set_s12, doc=_DOC_S12)
    s13 = property(_get_s13, _set_s13, doc=_DOC_S13)
    s23 = property(_get_s23, _set_s23, doc=_DOC_S23)

    wf_s1 = property(_get_wf_s1, _set_wf_s1, doc=_DOC_WF_S1)
    wf_s2 = property(_get_wf_s2, _set_wf_s2, doc=_DOC_WF_S2)
    wf_s3 = property(_get_wf_s3, _set_wf_s3, doc=_DOC_WF_S3)
    wf_s12 = property(_get_wf_s12, _set_wf_s12, doc=_DOC_WF_S12)

    wf_s13 = property(_get_wf_s13, _set_wf_s13, doc=_DOC_WF_S13)
    wf_s23 = property(_get_wf_s23, _set_wf_s23, doc=_DOC_WF_S23)


ATTRS_MAX_STRESS = inspect.signature(MaxStressCriterion).parameters.keys()
