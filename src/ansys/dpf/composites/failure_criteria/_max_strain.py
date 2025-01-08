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

"""Defines the MaxStrain failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_E1 = "Activates the failure evaluation regarding the strain in the material 1 direction."
_DOC_E2 = "Activates the failure evaluation regarding the strain in the material 2 direction."
_DOC_E3 = (
    "Activates the failure evaluation regarding the strain in the "
    "material 3 direction (out-of-plane)."
)
_DOC_E12 = "Whether to activate the failure evaluation regarding the in-plane shear strain e12."
_DOC_E13 = "Whether to activate the failure evaluation regarding the interlaminar shear strain e13."
_DOC_E23 = "Whether to activate the failure evaluation regarding the interlaminar shear strain e23."
_DOC_WF_E1 = "Weighting factor of the failure mode e1."
_DOC_WF_E2 = "Weighting factor of the failure mode e2."
_DOC_WF_E3 = "Weighting factor of the failure mode e3."
_DOC_WF_E12 = "Weighting factor of the failure mode e12."
_DOC_WF_E13 = "Weighting factor of the failure mode e13."
_DOC_WF_E23 = "Weighting factor of the failure mode e23."
_DOC_FORCE_GLOBAL_STRAIN_LIMITS = (
    "Whether to use one set of global strain limits instead of the "
    "strain limits of the materials."
)
_DOC_EXT = "Global tensile strain limit in material direction 1."
_DOC_EXC = "Global compressive strain limit in material direction 1."
_DOC_EYT = "Global tensile strain limit in material direction 2."
_DOC_EYC = "Global compressive strain limit in material direction 2."
_DOC_EZT = "Global strain limit in material direction 3."
_DOC_EZC = "Global compressive strain limit in material direction 3."
_DOC_ESXY = "Global strain limit in material direction 12."
_DOC_ESXZ = "Global strain limit in material direction 13."
_DOC_ESYZ = "Global strain limit in material direction 23."


class MaxStrainCriterion(FailureCriterionBase):
    """Max Strain Criterion."""

    __doc__ = f"""Defines the maximum strain failure criterion for orthotropic reinforced materials.

    Parameters
    ----------
    e1:
        {_DOC_E1}
    e2:
        {_DOC_E2}
    e3:
        {_DOC_E3}
    e12:
        {_DOC_E12}
    e13:
        {_DOC_E13}
    e23:
        {_DOC_E23}
    wf_e1:
        {_DOC_WF_E1}
    wf_e2:
        {_DOC_WF_E2}
    wf_e3:
        {_DOC_WF_E3}
    wf_e12:
        {_DOC_WF_E12}
    wf_e13:
        {_DOC_WF_E13}
    wf_e23:
        {_DOC_WF_E23}
    eXt:
        {_DOC_EXT}
    eXc:
        {_DOC_EXC}
    eYt:
        {_DOC_EYT}
    eYc:
        {_DOC_EYC}
    eZt:
        {_DOC_EZT}
    eZc:
        {_DOC_EZC}
    eSxy:
        {_DOC_ESXY}
    eSxz:
        {_DOC_ESXZ}
    eSyz:
        {_DOC_ESYZ}
    """

    def __init__(
        self,
        *,
        e1: bool = True,
        e2: bool = True,
        e3: bool = False,
        e12: bool = True,
        e13: bool = False,
        e23: bool = False,
        wf_e1: float = 1.0,
        wf_e2: float = 1.0,
        wf_e3: float = 1.0,
        wf_e12: float = 1.0,
        wf_e13: float = 1.0,
        wf_e23: float = 1.0,
        force_global_strain_limits: bool = False,
        eXt: float = 0.0,
        eXc: float = 0.0,
        eYt: float = 0.0,
        eYc: float = 0.0,
        eZt: float = 0.0,
        eZc: float = 0.0,
        eSxy: float = 0.0,
        eSxz: float = 0.0,
        eSyz: float = 0.0,
    ):
        """Create a maximum strain failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Max Strain", active=True)

        for attr in ATTRS_MAX_STRAIN:
            setattr(self, attr, eval(attr))

    def _get_e1(self) -> bool:
        return self._e1

    def _set_e1(self, value: bool) -> None:
        self._e1 = value

    def _get_e2(self) -> bool:
        return self._e2

    def _set_e2(self, value: bool) -> None:
        self._e2 = value

    def _get_e3(self) -> bool:
        return self._e3

    def _set_e3(self, value: bool) -> None:
        self._e3 = value

    def _get_e12(self) -> bool:
        return self._e12

    def _set_e12(self, value: bool) -> None:
        self._e12 = value

    def _get_e13(self) -> bool:
        return self._e13

    def _set_e13(self, value: bool) -> None:
        self._e13 = value

    def _get_e23(self) -> bool:
        return self._e23

    def _set_e23(self, value: bool) -> None:
        self._e23 = value

    def _get_wf_e1(self) -> float:
        return self._wf_e1

    def _set_wf_e1(self, value: float) -> None:
        self._wf_e1 = value

    def _get_wf_e2(self) -> float:
        return self._wf_e2

    def _set_wf_e2(self, value: float) -> None:
        self._wf_e2 = value

    def _get_wf_e3(self) -> float:
        return self._wf_e3

    def _set_wf_e3(self, value: float) -> None:
        self._wf_e3 = value

    def _get_wf_e12(self) -> float:
        return self._wf_e12

    def _set_wf_e12(self, value: float) -> None:
        self._wf_e12 = value

    def _get_wf_e13(self) -> float:
        return self._wf_e13

    def _set_wf_e13(self, value: float) -> None:
        self._wf_e13 = value

    def _get_wf_e23(self) -> float:
        return self._wf_e23

    def _set_wf_e23(self, value: float) -> None:
        self._wf_e23 = value

    def _get_force_global_strain_limits(self) -> bool:
        return self._force_global_strain_limits

    def _set_force_global_strain_limits(self, value: bool) -> None:
        self._force_global_strain_limits = value

    def _get_eXt(self) -> float:
        return self._eXt

    def _set_eXt(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Tensile limit eXt cannot be negative.")
        self._eXt = value

    def _get_eXc(self) -> float:
        return self._eXc

    def _set_eXc(self, value: float) -> None:
        if value > 0.0:
            raise ValueError("Compressive limit eXc cannot be positive.")
        self._eXc = value

    def _get_eYt(self) -> float:
        return self._eYt

    def _set_eYt(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Tensile limit eYt cannot be negative.")
        self._eYt = value

    def _get_eYc(self) -> float:
        return self._eYc

    def _set_eYc(self, value: float) -> None:
        if value > 0.0:
            raise ValueError("Compressive limit eYc cannot be positive.")
        self._eYc = value

    def _get_eZt(self) -> float:
        return self._eZt

    def _set_eZt(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Tensile limit eZt cannot be negative.")
        self._eZt = value

    def _get_eZc(self) -> float:
        return self._eZc

    def _set_eZc(self, value: float) -> None:
        if value > 0.0:
            raise ValueError("Compressive limit eZc cannot be positive.")
        self._eZc = value

    def _get_eSxy(self) -> float:
        return self._eSxy

    def _set_eSxy(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Strain limit eSxy cannot be negative.")
        self._eSxy = value

    def _get_eSxz(self) -> float:
        return self._eSxz

    def _set_eSxz(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Strain limit eSxz cannot be negative.")
        self._eSxz = value

    def _get_eSyz(self) -> float:
        return self._eSyz

    def _set_eSyz(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("Strain limit eSyz cannot be negative.")
        self._eSyz = value

    e1 = property(_get_e1, _set_e1, doc=_DOC_E1)
    e2 = property(_get_e2, _set_e2, doc=_DOC_E2)

    e3 = property(_get_e3, _set_e3, doc=_DOC_E3)
    e12 = property(_get_e12, _set_e12, doc=_DOC_E12)
    e13 = property(_get_e13, _set_e13, doc=_DOC_E13)
    e23 = property(_get_e23, _set_e23, doc=_DOC_E23)

    wf_e1 = property(_get_wf_e1, _set_wf_e1, doc=_DOC_WF_E1)
    wf_e2 = property(_get_wf_e2, _set_wf_e2, doc=_DOC_WF_E2)
    wf_e3 = property(_get_wf_e3, _set_wf_e3, doc=_DOC_WF_E3)
    wf_e12 = property(_get_wf_e12, _set_wf_e12, doc=_DOC_WF_E12)
    wf_e13 = property(_get_wf_e13, _set_wf_e13, doc=_DOC_WF_E13)
    wf_e23 = property(_get_wf_e23, _set_wf_e23, doc=_DOC_WF_E23)

    force_global_strain_limits = property(
        _get_force_global_strain_limits,
        _set_force_global_strain_limits,
        doc=_DOC_FORCE_GLOBAL_STRAIN_LIMITS,
    )
    eXt = property(_get_eXt, _set_eXt, doc=_DOC_EXT)
    eXc = property(_get_eXc, _set_eXc, doc=_DOC_EXC)
    eYt = property(_get_eYt, _set_eYt, doc=_DOC_EYT)
    eYc = property(_get_eYc, _set_eYc, doc=_DOC_EXC)
    eZt = property(_get_eZt, _set_eZt, doc=_DOC_EZT)
    eZc = property(_get_eZc, _set_eZc, doc=_DOC_EZC)
    eSxy = property(_get_eSxy, _set_eSxy, doc=_DOC_ESXY)

    eSxz = property(_get_eSxz, _set_eSxz, doc=_DOC_ESXZ)
    eSyz = property(_get_eSyz, _set_eSyz, doc=_DOC_ESYZ)


ATTRS_MAX_STRAIN = inspect.signature(MaxStrainCriterion).parameters.keys()
