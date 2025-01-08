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

"""Puck Failure Criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_PF = "Whether to activate the failure evaluation regarding fiber failure."
_DOC_PMA = "Whether to activate the failure evaluation regarding matrix failure due to tension."
_DOC_PMB = "Whether to activate the failure evaluation regarding matrix failure due to compression."
_DOC_PMC = (
    "Whether to activate the failure evaluation regarding matrix failure due to shear failure."
)
_DOC_PD = "Whether to activate the failure evaluation regarding delamination if dim is equal to 3."
_DOC_DIM = (
    "Whether the 2D or 3D formulation of the criterion is used. The latter one also "
    "supports the failure mode delamination. Use ``1`` for a simplified Puck criterion."
)
_DOC_WF_PF = "Weighting factor of the fiber failure (pf) mode."
_DOC_WF_PMA = "Weighting factor of the matrix failure (pma) mode."
_DOC_WF_PMB = "Weighting factor of the matrix failure (pmb) mode."
_DOC_WF_PMC = "Weighting factor of the matrix failure (pmc) mode."
_DOC_WF_PD = "Weighting factor of the delamination failure (pd) mode."
_DOC_CFPS = "Whether to consider inter-fiber strength reduction due to fiber parallel stresses."
_DOC_S = (
    "Specifies the effect of fiber parallel stresses regarding inter-fiber failure. "
    "s = [0, 1) and the default is ``0.5``."
)
_DOC_M = (
    "Specifies the effect of fiber parallel stresses regarding inter-fiber failure. "
    "M = [0, 1). The default is ``0.5``."
)
_DOC_INTERFACE_WEAKENING_FACTOR = (
    "Multiplicator for the interlaminar strength if "
    "failure mode ``pd`` is active. The default is ``0.8``."
)
_DOC_FORCE_GLOBAL_CONSTANTS = (
    "Whether to use global constants instead of the material-wise properties."
)
_DOC_P21_NEG = (
    "Global inclination factor in the"
    r" :math:`\sigma_1 - \tau_{12}` plane at :math:`\sigma_2 = 0` for compression."
)
_DOC_P21_POS = (
    "Global inclination factor in the"
    r" :math:`\sigma_1 - \tau_{12}` plane at :math:`\sigma_2 = 0` for tension."
)
_DOC_P22_NEG = (
    r"Global inclination factor of the fracture  plane :math:`\perp \perp` for compression."
)
_DOC_P22_POS = r"Global inclination factor of the fracture plane :math:`\perp \perp` for tension."


class PuckCriterion(FailureCriterionBase):
    """Puck Criterion."""

    __doc__ = f"""Defines the Puck failure criterion for UD reinforced materials.

    Parameters
    ----------
    pf:
        {_DOC_PF}
    pma:
        {_DOC_PMA}
    pmb:
        {_DOC_PMB}
    pmc:
        {_DOC_PMC}
    pd:
        {_DOC_PD}
    dim:
        {_DOC_DIM}
    wf_pf:
        {_DOC_WF_PF}
    wf_pma:
        {_DOC_WF_PMA}
    wf_pmb:
        {_DOC_WF_PMB}
    wf_pmc:
        {_DOC_WF_PMC}
    wf_pd:
        {_DOC_WF_PD}
    cfps:
        {_DOC_CFPS}
    s:
        {_DOC_S}
    m:
        {_DOC_M}
    interface_weakening_factor:
        {_DOC_INTERFACE_WEAKENING_FACTOR}
    force_global_constants:
        {_DOC_FORCE_GLOBAL_CONSTANTS}
    p21_neg:
        {_DOC_P21_NEG}
    p21_pos:
        {_DOC_P21_POS},
    p22_neg:
        {_DOC_P22_NEG}
    p22_pos:
        {_DOC_P22_POS}
    """

    def __init__(
        self,
        *,
        pf: bool = True,
        pma: bool = True,
        pmb: bool = True,
        pmc: bool = True,
        pd: bool = False,
        dim: int = 2,
        wf_pf: float = 1.0,
        wf_pma: float = 1.0,
        wf_pmb: float = 1.0,
        wf_pmc: float = 1.0,
        wf_pd: float = 1.0,
        cfps: bool = True,
        s: float = 0.5,
        M: float = 0.5,
        interface_weakening_factor: float = 0.8,
        force_global_constants: bool = False,
        p21_neg: float = 0.275,
        p21_pos: float = 0.325,
        p22_neg: float = 0.225,
        p22_pos: float = 0.225,
    ):
        """Create a Puck failure criterion.

        Can be used in combination with uni-directional orthotropic reinforced materials.
        """
        super().__init__(name="Puck", active=True)

        for attr in ATTRS_PUCK:
            setattr(self, attr, eval(attr))

    def _get_pf(self) -> bool:
        return self._pf

    def _set_pf(self, value: bool) -> None:
        self._pf = value

    def _get_pma(self) -> bool:
        return self._pma

    def _set_pma(self, value: bool) -> None:
        self._pma = value

    def _get_pmb(self) -> bool:
        return self._pmb

    def _set_pmb(self, value: bool) -> None:
        self._pmb = value

    def _get_pmc(self) -> bool:
        return self._pmc

    def _set_pmc(self, value: bool) -> None:
        self._pmc = value

    def _get_pd(self) -> bool:
        return self._pd

    def _set_pd(self, value: bool) -> None:
        self._pd = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [1, 2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 1, 2 or 3."
            )

    def _get_wf_pf(self) -> float:
        return self._wf_pf

    def _set_wf_pf(self, value: float) -> None:
        self._wf_pf = value

    def _get_wf_pma(self) -> float:
        return self._wf_pma

    def _set_wf_pma(self, value: float) -> None:
        self._wf_pma = value

    def _get_wf_pmb(self) -> float:
        return self._wf_pmb

    def _set_wf_pmb(self, value: float) -> None:
        self._wf_pmb = value

    def _get_wf_pmc(self) -> float:
        return self._wf_pmc

    def _set_wf_pmc(self, value: float) -> None:
        self._wf_pmc = value

    def _get_wf_pd(self) -> float:
        return self._wf_pd

    def _set_wf_pd(self, value: float) -> None:
        self._wf_pd = value

    def _get_cfps(self) -> bool:
        return self._cfps

    def _set_cfps(self, value: bool) -> None:
        self._cfps = value

    def _get_s(self) -> float:
        return self._s

    def _set_s(self, value: float) -> None:
        if value < 0.0 or value >= 1.0:
            raise AttributeError(f"Parameter s cannot be set to {value}. Allowed range: [0, 1).")
        self._s = value

    def _get_m(self) -> float:
        return self._M

    def _set_m(self, value: float) -> None:
        if value < 0.0 or value >= 1.0:
            raise AttributeError(f"Parameter M cannot be set to {value}. Allowed range: [0, 1).")
        self._M = value

    def _get_interface_weakening_factor(self) -> float:
        return self._interface_weakening_factor

    def _set_interface_weakening_factor(self, value: float) -> None:
        self._interface_weakening_factor = value

    def _get_force_global_constants(self) -> bool:
        return self._force_global_constants

    def _set_force_global_constants(self, value: bool) -> None:
        self._force_global_constants = value

    def _get_p21_neg(self) -> float:
        return self._p21_neg

    def _set_p21_neg(self, value: float) -> None:
        self._p21_neg = value

    def _get_p21_pos(self) -> float:
        return self._p21_pos

    def _set_p21_pos(self, value: float) -> None:
        self._p21_pos = value

    def _get_p22_neg(self) -> float:
        return self._p22_neg

    def _set_p22_neg(self, value: float) -> None:
        self._p22_neg = value

    def _get_p22_pos(self) -> float:
        return self._p22_pos

    def _set_p22_pos(self, value: float) -> None:
        self._p22_pos = value

    pf = property(_get_pf, _set_pf, doc=_DOC_PF)
    pma = property(
        _get_pma,
        _set_pma,
        doc=_DOC_PMA,
    )
    pmb = property(
        _get_pmb,
        _set_pmb,
        doc=_DOC_PMB,
    )
    pmc = property(_get_pmc, _set_pmc, doc=_DOC_PMC)
    pd = property(
        _get_pd,
        _set_pd,
        doc=_DOC_PD,
    )
    dim = property(
        _get_dim,
        _set_dim,
        doc=_DOC_DIM,
    )

    wf_pf = property(_get_wf_pf, _set_wf_pf, doc=_DOC_WF_PF)
    wf_pma = property(_get_wf_pma, _set_wf_pma, doc=_DOC_WF_PMA)
    wf_pmb = property(_get_wf_pmb, _set_wf_pmb, doc=_DOC_WF_PMB)
    wf_pmc = property(_get_wf_pmc, _set_wf_pmc, doc=_DOC_WF_PMC)
    wf_pd = property(_get_wf_pd, _set_wf_pd, doc=_DOC_WF_PD)
    cfps = property(
        _get_cfps,
        _set_cfps,
        doc=_DOC_CFPS,
    )

    s = property(
        _get_s,
        _set_s,
        doc=_DOC_S,
    )
    M = property(
        _get_m,
        _set_m,
        doc=_DOC_M,
    )

    interface_weakening_factor = property(
        _get_interface_weakening_factor,
        _set_interface_weakening_factor,
        doc=_DOC_INTERFACE_WEAKENING_FACTOR,
    )

    force_global_constants = property(
        _get_force_global_constants,
        _set_force_global_constants,
        doc=_DOC_FORCE_GLOBAL_CONSTANTS,
    )

    p21_neg = property(
        _get_p21_neg,
        _set_p21_neg,
        doc=_DOC_P21_NEG,
    )
    p21_pos = property(_get_p21_pos, _set_p21_pos, doc=_DOC_P21_POS)
    p22_neg = property(
        _get_p22_neg,
        _set_p22_neg,
        doc=_DOC_P22_NEG,
    )
    p22_pos = property(
        _get_p22_pos,
        _set_p22_pos,
        doc=_DOC_P22_POS,
    )


ATTRS_PUCK = inspect.signature(PuckCriterion).parameters.keys()
