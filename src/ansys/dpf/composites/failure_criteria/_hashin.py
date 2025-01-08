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

"""Hashin failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_HF = "Whether to activate the failure evaluation regarding fiber failure."
_DOC_HM = "Whether to activate the failure evaluation regarding matrix failure."
_DOC_HD = "Whether to activate the failure evaluation regarding delamination if dim is equal to 3."
_DOC_DIM = (
    "Whether the 2D or 3D formulation of the criterion is used. The latter one also "
    "supports the failure mode delamination."
)
_DOC_WF_HF = "Weighting factor of the fiber failure (hf) mode."
_DOC_WF_HM = "Weighting factor of the matrix failure (hm) mode."
_DOC_WF_HD = "Weighting factor of the delamination (hd) mode."


class HashinCriterion(FailureCriterionBase):
    """Hashin Criterion."""

    __doc__ = f"""Defines the Hashin failure criterion for UD reinforced materials.

    Parameters
    ----------
    hf :
        {_DOC_HF}
    hm :
        {_DOC_HM}
    hd :
        {_DOC_HD}
    dim :
        {_DOC_DIM}
    wf_hf :
        {_DOC_WF_HF}
    wf_hm :
        {_DOC_WF_HM}
    wf_hd :
        {_DOC_WF_HD}

    """

    def __init__(
        self,
        *,
        hf: bool = True,
        hm: bool = True,
        hd: bool = False,
        dim: int = 2,
        wf_hf: float = 1.0,
        wf_hm: float = 1.0,
        wf_hd: float = 1.0,
    ):
        """Create a Hashin failure criterion.

        Can be used in combination with uni-directional orthotropic reinforced materials.
        """
        super().__init__(name="Hashin", active=True)

        for attr in ATTRS_HASHIN:
            setattr(self, attr, eval(attr))

    def _get_hf(self) -> bool:
        return self._hf

    def _set_hf(self, value: bool) -> None:
        self._hf = value

    def _get_hm(self) -> bool:
        return self._hm

    def _set_hm(self, value: bool) -> None:
        self._hm = value

    def _get_hd(self) -> bool:
        return self._hd

    def _set_hd(self, value: bool) -> None:
        self._hd = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3."
            )

    def _get_wf_hf(self) -> float:
        return self._wf_hf

    def _set_wf_hf(self, value: float) -> None:
        self._wf_hf = value

    def _get_wf_hm(self) -> float:
        return self._wf_hm

    def _set_wf_hm(self, value: float) -> None:
        self._wf_hm = value

    def _get_wf_hd(self) -> float:
        return self._wf_hd

    def _set_wf_hd(self, value: float) -> None:
        self._wf_hd = value

    hf = property(_get_hf, _set_hf, doc=_DOC_HF)
    hm = property(_get_hm, _set_hm, doc=_DOC_HM)
    hd = property(
        _get_hd,
        _set_hd,
        doc=_DOC_HD,
    )
    dim = property(
        _get_dim,
        _set_dim,
        doc=_DOC_DIM,
    )
    wf_hf = property(_get_wf_hf, _set_wf_hf, doc=_DOC_HF)
    wf_hm = property(_get_wf_hm, _set_wf_hm, doc=_DOC_HM)
    wf_hd = property(_get_wf_hd, _set_wf_hd, doc=_DOC_HD)


ATTRS_HASHIN = inspect.signature(HashinCriterion).parameters.keys()
