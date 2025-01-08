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

"""Cuntze failure criterion."""

import inspect
import math

from ._failure_criterion_base import FailureCriterionBase

_DOC_CFC = "Activates the failure evaluation regarding compression in fiber direction."
_DOC_CFT = "Activates the failure evaluation regarding tension in fiber direction."
_DOC_CMA = "Activates the failure evaluation of the matrix due to tension."
_DOC_CMB = "Activates the failure evaluation of the matrix due to compression."
_DOC_CMC = "Activates the failure evaluation of the matrix due to compression or shear."
_DOC_DIM = "Whether the 2D or 3D formulation of the criterion is used."
_DOC_WF_CFC = "Weighting factor of fiber failure due to compression (cfc)."
_DOC_WF_CFT = "Weighting factor of fiber failure due to tension (cft)."
_DOC_WF_CMA = "Weighting factor of matrix failure due to tension (cma)."
_DOC_WF_CMB = "Weighting factor of matrix failure due to compression (cmb)."
_DOC_WF_CMC = "Weighting factor of matrix failure due to compression or shear (cmc)."
_DOC_B21 = "In-plane shear friction coefficient. The default is ``0.2``."
_DOC_B32 = (
    "Out-of-plane shear friction coefficient. The default is ``1.3805``. The value depends "
    "on the fracture plane angle."
)
_DOC_MODE_INTERACTION_COEFF = "Mode interaction coefficient. The default is ``2.6``."
_DOC_FRACTURE_PLANE_ANGLE = (
    "Fracture plane angle in degrees. The default is ``53``. "
    "The value must be greater than 45. The value depends on the out-of-plane "
    "shear friction coefficient."
)


class CuntzeCriterion(FailureCriterionBase):
    """Provides the Cuntze criterion."""

    __doc__ = f"""Defines the Cuntze criterion for uni-directional orthotropic reinforced materials.

    Parameters
    ----------
    cfc:
        {_DOC_CFC}
    cft:
        {_DOC_CFT}
    cma:
        {_DOC_CMA}
    cmb:
        {_DOC_CMB}
    cmc:
        {_DOC_CMC}
    dim:
        {_DOC_DIM}
    wf_cfc:
        {_DOC_WF_CFC}
    wf_cft:
        {_DOC_WF_CFT}
    wf_cma:
        {_DOC_WF_CMA}
    wf_cmb:
        {_DOC_WF_CMB}
    wf_cmc:
        {_DOC_WF_CMC}
    b21:
        {_DOC_B21}
    b32:
        {_DOC_B32}
    fracture_plane_angle:
        {_DOC_FRACTURE_PLANE_ANGLE}
    mode_interaction_coeff:
        {_DOC_MODE_INTERACTION_COEFF}
    """

    def __init__(
        self,
        *,
        cfc: bool = True,
        cft: bool = True,
        cma: bool = True,
        cmb: bool = True,
        cmc: bool = True,
        dim: int = 2,
        wf_cfc: float = 1.0,
        wf_cft: float = 1.0,
        wf_cma: float = 1.0,
        wf_cmb: float = 1.0,
        wf_cmc: float = 1.0,
        b21: float = 0.2,
        b32: float = 1.3805,
        fracture_plane_angle: float = 53.0,
        mode_interaction_coeff: float = 2.6,
    ) -> None:
        """Construct a Cuntze failure criterion."""
        super().__init__(name="Cuntze", active=True)

        for attr in ATTRS_CUNTZE:
            setattr(self, attr, eval(attr))

    def _get_cfc(self) -> bool:
        return self._cfc

    def _set_cfc(self, value: bool) -> None:
        self._cfc = value

    def _get_cft(self) -> bool:
        return self._cft

    def _set_cft(self, value: bool) -> None:
        self._cft = value

    def _get_cma(self) -> bool:
        return self._cma

    def _set_cma(self, value: bool) -> None:
        self._cma = value

    def _get_cmb(self) -> bool:
        return self._cmb

    def _set_cmb(self, value: bool) -> None:
        self._cmb = value

    def _get_cmc(self) -> bool:
        return self._cmc

    def _set_cmc(self, value: bool) -> None:
        self._cmc = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. The values allowed are 2 or 3."
            )

    def _get_wf_cfc(self) -> float:
        return self._wf_cfc

    def _set_wf_cfc(self, value: float) -> None:
        self._wf_cfc = value

    def _get_wf_cft(self) -> float:
        return self._wf_cft

    def _set_wf_cft(self, value: float) -> None:
        self._wf_cft = value

    def _get_wf_cma(self) -> float:
        return self._wf_cma

    def _set_wf_cma(self, value: float) -> None:
        self._wf_cma = value

    def _get_wf_cmb(self) -> float:
        return self._wf_cmb

    def _set_wf_cmb(self, value: float) -> None:
        self._wf_cmb = value

    def _get_wf_cmc(self) -> float:
        return self._wf_cmc

    def _set_wf_cmc(self, value: float) -> None:
        self._wf_cmc = value

    def _get_b21(self) -> float:
        return self._b21

    def _set_b21(self, value: float) -> None:
        self._b21 = value

    def _get_b32(self) -> float:
        return self._b32

    def _set_b32(self, value: float) -> None:
        if value >= 1.0:
            self._fracture_plane_angle = math.acos(1.0 / value - 1.0) / 2.0 * 180.0 / math.pi
            self._b32 = value
        else:
            raise ValueError("Out-of-plane friction coefficient b32 must be 1 or greater.")

    def _get_fracture_plane_angle(self) -> float:
        return self._fracture_plane_angle

    def _set_fracture_plane_angle(self, value: float) -> None:
        if value > 45.0:
            self._b32 = 1.0 / (1.0 + math.cos(2.0 * math.pi * value / 180.0))
            self._fracture_plane_angle = value
        else:
            raise ValueError("Fracture plane angle must be above 45 degrees.")

    def _get_mode_interaction_coeff(self) -> float:
        return self._mode_interaction_coeff

    def _set_mode_interaction_coeff(self, value: float) -> None:
        self._mode_interaction_coeff = value

    cfc = property(_get_cfc, _set_cfc, doc=_DOC_CFC)
    cft = property(_get_cft, _set_cft, doc=_DOC_CFT)
    cma = property(_get_cma, _set_cma, doc=_DOC_CMA)
    cmb = property(_get_cmb, _set_cmb, doc=_DOC_CMB)
    cmc = property(_get_cmc, _set_cmc, doc=_DOC_CMC)
    dim = property(_get_dim, _set_dim, doc=_DOC_DIM)
    wf_cfc = property(_get_wf_cfc, _set_wf_cfc, doc=_DOC_WF_CFC)
    wf_cft = property(_get_wf_cft, _set_wf_cft, doc=_DOC_WF_CFT)
    wf_cma = property(_get_wf_cma, _set_wf_cma, doc=_DOC_WF_CMA)
    wf_cmb = property(_get_wf_cmb, _set_wf_cmb, doc=_DOC_WF_CMB)
    wf_cmc = property(_get_wf_cmc, _set_wf_cmc, doc=_DOC_WF_CMC)
    b21 = property(_get_b21, _set_b21, doc=_DOC_B21)
    b32 = property(_get_b32, _set_b32, doc=_DOC_B32)
    mode_interaction_coeff = property(
        _get_mode_interaction_coeff,
        _set_mode_interaction_coeff,
        doc=_DOC_MODE_INTERACTION_COEFF,
    )
    fracture_plane_angle = property(
        _get_fracture_plane_angle,
        _set_fracture_plane_angle,
        doc=_DOC_FRACTURE_PLANE_ANGLE,
    )


ATTRS_CUNTZE = inspect.signature(CuntzeCriterion).parameters.keys()
