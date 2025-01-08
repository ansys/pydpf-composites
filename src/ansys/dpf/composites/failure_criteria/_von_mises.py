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

"""Von Mises Criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_VME = "Whether to activate the von Mises strain criterion."
_DOC_VMS = "Whether to activate the von Mises stress criterion."
_DOC_WF_VME = "Weighting factor of the strain criterion (vme)."
_DOC_WF_VMS = "Weighting factor of the stress criterion (vms)."
_DOC_EVAL_INS = (
    "Whether to consider interlaminar normal stresses (s3) and compute them for layered shells."
)


class VonMisesCriterion(FailureCriterionBase):
    """Von Mises criterion."""

    __doc__ = f"""Defines the von Mises criterion for isotropic materials.

    Parameters
    ----------
    vme:
        {_DOC_VME}
    vms:
        {_DOC_VMS}
    wf_vme:
        {_DOC_WF_VME}
    wf_vms:
        {_DOC_WF_VMS}
    eval_ins:
        {_DOC_EVAL_INS}
    """

    def __init__(
        self,
        *,
        vme: bool = True,
        vms: bool = True,
        wf_vme: float = 1.0,
        wf_vms: float = 1.0,
        eval_ins: bool = False,
    ):
        """Create a von Mises criterion."""
        super().__init__(name="Von Mises", active=True)

        for attr in ATTRS_VON_MISES:
            setattr(self, attr, eval(attr))

    def _get_vme(self) -> bool:
        return self._vme

    def _set_vme(self, value: bool) -> None:
        self._vme = value

    def _get_vms(self) -> bool:
        return self._vms

    def _set_vms(self, value: bool) -> None:
        self._vms = value

    def _get_wf_vme(self) -> float:
        return self._wf_vme

    def _set_wf_vme(self, value: float) -> None:
        self._wf_vme = value

    def _get_wf_vms(self) -> float:
        return self._wf_vms

    def _set_wf_vms(self, value: float) -> None:
        self._wf_vms = value

    def _get_eval_ins(self) -> bool:
        return self._eval_ins

    def _set_eval_ins(self, value: bool) -> None:
        self._eval_ins = value

    vme = property(_get_vme, _set_vme, doc=_DOC_VME)
    vms = property(_get_vms, _set_vms, doc=_DOC_VMS)
    wf_vme = property(_get_wf_vme, _set_wf_vme, doc=_DOC_WF_VME)
    wf_vms = property(_get_wf_vms, _set_wf_vms, doc=_DOC_WF_VMS)

    eval_ins = property(
        _get_eval_ins,
        _set_eval_ins,
        doc=_DOC_EVAL_INS,
    )


ATTRS_VON_MISES = inspect.signature(VonMisesCriterion).parameters.keys()
