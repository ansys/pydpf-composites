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

"""LaRC failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_LFC = "Whether to activate the failure evaluation regarding compression in fiber direction."

_DOC_LFT = "Whether to activate the failure evaluation regarding tension in fiber direction."

_DOC_LMC = "Whether to activate the failure evaluation of the matrix due to compression."

_DOC_LMT = "Whether to activate the failure evaluation of the matrix due to tension."

_DOC_DIM = (
    "Whether the 2D or 3D formulation of the criterion is used. 2D is equivalent to "
    "LaRC03, and 3D is equivalent to LaRC04."
)
_DOC_WF_LFC = "Weighting factor of fiber failure due to compression (lfc)."
_DOC_WF_LFT = "Weighting factor of fiber failure due to tension (lft)."
_DOC_WF_LMC = "Weighting factor of matrix failure due to compression (lmc)."
_DOC_WF_LMT = "Weighting factor of matrix failure due to tension (lmt)."


class LaRCCriterion(FailureCriterionBase):
    """LaRC Criterion."""

    __doc__ = f"""Defines the LaRC failure criterion for UD reinforced materials.

    Parameters
    ----------
    lft:
        {_DOC_LFT}
    lfc:
        {_DOC_LFC}
    lmt:
        {_DOC_LMT}
    lmc:
        {_DOC_LMC}
    dim:
        {_DOC_DIM}
    wf_lft:
        {_DOC_WF_LFT}
    wf_lfc:
        {_DOC_WF_LFC}
    wf_lmt:
        {_DOC_WF_LMT}
    wf_lmc:
        {_DOC_WF_LMC}
    """

    def __init__(
        self,
        *,
        lft: bool = True,
        lfc: bool = True,
        lmt: bool = True,
        lmc: bool = True,
        dim: int = 2,
        wf_lft: float = 1.0,
        wf_lfc: float = 1.0,
        wf_lmt: float = 1.0,
        wf_lmc: float = 1.0,
    ):
        """Create a LaRC failure criterion for uni-directional reinforced materials."""
        super().__init__(name="LaRC", active=True)

        for attr in ATTRS_LARC:
            setattr(self, attr, eval(attr))

    def _get_lfc(self) -> bool:
        return self._lfc

    def _set_lfc(self, value: bool) -> None:
        self._lfc = value

    def _get_lft(self) -> bool:
        return self._lft

    def _set_lft(self, value: bool) -> None:
        self._lft = value

    def _get_lmc(self) -> bool:
        return self._lmc

    def _set_lmc(self, value: bool) -> None:
        self._lmc = value

    def _get_lmt(self) -> bool:
        return self._lmt

    def _set_lmt(self, value: bool) -> None:
        self._lmt = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3 for "
                f" LaRC03 and LaRC04 respectively."
            )

    def _get_wf_lfc(self) -> float:
        return self._wf_lfc

    def _set_wf_lfc(self, value: float) -> None:
        self._wf_lfc = value

    def _get_wf_lft(self) -> float:
        return self._wf_lft

    def _set_wf_lft(self, value: float) -> None:
        self._wf_lft = value

    def _get_wf_lmc(self) -> float:
        return self._wf_lmc

    def _set_wf_lmc(self, value: float) -> None:
        self._wf_lmc = value

    def _get_wf_lmt(self) -> float:
        return self._wf_lmt

    def _set_wf_lmt(self, value: float) -> None:
        self._wf_lmt = value

    lfc = property(
        _get_lfc,
        _set_lfc,
        doc=_DOC_LFC,
    )
    lft = property(
        _get_lft,
        _set_lft,
        doc=_DOC_LFT,
    )
    lmc = property(_get_lmc, _set_lmc, doc=_DOC_LMC)
    lmt = property(_get_lmt, _set_lmt, doc=_DOC_LMT)

    dim = property(
        _get_dim,
        _set_dim,
        doc=_DOC_DIM,
    )

    wf_lfc = property(_get_wf_lfc, _set_wf_lfc, doc=_DOC_WF_LFC)

    wf_lft = property(_get_wf_lft, _set_wf_lft, doc=_DOC_WF_LFT)

    wf_lmc = property(_get_wf_lmc, _set_wf_lmc, doc=_DOC_WF_LMC)
    wf_lmt = property(_get_wf_lmt, _set_wf_lmt, doc=_DOC_WF_LMT)


ATTRS_LARC = inspect.signature(LaRCCriterion).parameters.keys()
