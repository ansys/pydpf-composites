from .failure_criterion_base import FailureCriterionBase

ATTRS_PUCK = [
    "pf",
    "pma",
    "pmb",
    "pmc",
    "pd",
    "dim",
    "wf_pf",
    "wf_pma",
    "wf_pmb",
    "wf_pmc",
    "wf_pd",
    "cfps",
    "s",
    "M",
    "interface_weakening_factor",
    "force_global_constants",
    "p21_neg",
    "p21_pos",
    "p22_neg",
    "p22_pos",
]


class PuckCriterion(FailureCriterionBase):
    """
    Defines the Puck failure criterion for uni-directional orthotropic reinforced materials.
    """

    def __init__(
        self,
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

        super().__init__(name="Puck", active=True)

        for attr in ATTRS_PUCK:
            setattr(self, attr, eval(attr))

    def _get_pf(self) -> bool:
        return self._pf

    def _set_pf(self, value: bool):
        self._pf = value

    def _get_pma(self) -> bool:
        return self._pma

    def _set_pma(self, value: bool):
        self._pma = value

    def _get_pmb(self) -> bool:
        return self._pmb

    def _set_pmb(self, value: bool):
        self._pmb = value

    def _get_pmc(self) -> bool:
        return self._pmc

    def _set_pmc(self, value: bool):
        self._pmc = value

    def _get_pd(self) -> bool:
        return self._pd

    def _set_pd(self, value: bool):
        self._pd = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int):
        if value in [1, 2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 1, 2 or 3."
            )

    def _get_wf_pf(self) -> float:
        return self._wf_pf

    def _set_wf_pf(self, value: float):
        self._wf_pf = value

    def _get_wf_pma(self) -> float:
        return self._wf_pma

    def _set_wf_pma(self, value: float):
        self._wf_pma = value

    def _get_wf_pmb(self) -> float:
        return self._wf_pmb

    def _set_wf_pmb(self, value: float):
        self._wf_pmb = value

    def _get_wf_pmc(self) -> float:
        return self._wf_pmc

    def _set_wf_pmc(self, value: float):
        self._wf_pmc = value

    def _get_wf_pd(self) -> float:
        return self._wf_pd

    def _set_wf_pd(self, value: float):
        self._wf_pd = value

    def _get_cfps(self) -> float:
        return self._cfps

    def _set_cfps(self, value: float):
        self._cfps = value

    def _get_s(self) -> float:
        return self._s

    def _set_s(self, value: float):
        if value < 0.0 or value >= 1.0:
            raise AttributeError(f"Parameter s cannot be set to {value}. Allowed range: [0, 1).")
        self._s = value

    def _get_m(self) -> float:
        return self._M

    def _set_m(self, value: float):
        if value < 0.0 or value >= 1.0:
            raise AttributeError(f"Parameter M cannot be set to {value}. Allowed range: [0, 1).")
        self._M = value

    def _get_interface_weakening_factor(self) -> float:
        return self._interface_weakening_factor

    def _set_interface_weakening_factor(self, value: float):
        self._interface_weakening_factor = value

    def _get_force_global_constants(self) -> bool:
        return self._force_global_constants

    def _set_force_global_constants(self, value: bool):
        self._force_global_constants = value

    def _get_p21_neg(self) -> float:
        return self._p21_neg

    def _set_p21_neg(self, value: float):
        self._p21_neg = value

    def _get_p21_pos(self) -> float:
        return self._p21_pos

    def _set_p21_pos(self, value: float):
        self._p21_pos = value

    def _get_p22_neg(self) -> float:
        return self._p22_neg

    def _set_p22_neg(self, value: float):
        self._p22_neg = value

    def _get_p22_pos(self) -> float:
        return self._p22_pos

    def _set_p22_pos(self, value: float):
        self._p22_pos = value

    pf = property(_get_pf,
                  _set_pf,
                  doc="Activates the failure evaluation regarding fiber failure.")
    pma = property(
        _get_pma,
        _set_pma,
        doc="Activates the failure evaluation regarding matrix failure due to tension.",
    )
    pmb = property(
        _get_pmb,
        _set_pmb,
        doc="Activates the failure evaluation regarding matrix failure due to compression.",
    )
    pmc = property(
        _get_pmc,
        _set_pmc,
        doc="Activates the failure evaluation regarding matrix failure due to shear failure.",
    )
    pd = property(
        _get_pd,
        _set_pd,
        doc="Activates the failure evaluation regarding delamination if dim is equal to 3.",
    )
    dim = property(
        _get_dim,
        _set_dim,
        doc="Whether the 2D or 3D formulation of the criterion is used. The latter one also "
        "supports the failure mode delamination. Use 1 for a simplified Puck criterion.",
    )
    wf_pf = property(
        _get_wf_pf,
        _set_wf_pf,
        doc="Weighting factor of the fiber failure (pf) mode.")
    wf_pma = property(
        _get_wf_pma, _set_wf_pma, doc="Weighting factor of the matrix failure (pma) mode."
    )
    wf_pmb = property(
        _get_wf_pmb, _set_wf_pmb, doc="Weighting factor of the matrix failure (pmb) mode."
    )
    wf_pmc = property(
        _get_wf_pmc, _set_wf_pmc, doc="Weighting factor of the matrix failure (pmc) mode."
    )
    wf_pd = property(
        _get_wf_pd, _set_wf_pd, doc="Weighting factor of the delamination failure (pd) mode."
    )
    cfps = property(
        _get_cfps,
        _set_cfps,
        doc="Whether to consider inter-fiber strength reduction due to fiber parallel stresses.",
    )
    s = property(
        _get_s,
        _set_s,
        doc="Specifies the effect of fiber parallel stresses regarding inter-fiber failure. "
        "s = [0, 1) and default is 0.5.",
    )
    M = property(
        _get_m,
        _set_m,
        doc="Specifies the effect of fiber parallel stresses regarding inter-fiber failure. "
        "M = [0, 1) and default is 0.5.",
    )
    interface_weakening_factor = property(
        _get_interface_weakening_factor,
        _set_interface_weakening_factor,
        doc="Multiplicator for the interlaminar strength if failure mode pd is active. "
            "Default is 0.8.",
    )

    force_global_constants = property(
        _get_force_global_constants,
        _set_force_global_constants,
        doc="Whether to use global constants instead of the material-wise properties.",
    )

    p21_neg = property(
        _get_p21_neg,
        _set_p21_neg,
        doc=f"Global inclination factor at \u03C3 2 = 0 for \u03C3 2 < 0",
    )
    p21_pos = property(
        _get_p21_pos,
        _set_p21_pos,
        doc=f"Global inclination factor at \u03C3 2 =0 for \u03C3 2 > 0"
    )
    p22_neg = property(
        _get_p22_neg,
        _set_p22_neg,
        doc=f"Global inclination factor of the fracture plane \u27c2 \u27c2.",
    )
    p22_pos = property(
        _get_p22_pos,
        _set_p22_pos,
        doc=f"Global inclination factor of the fracture plane \u27c2 \u27c2.",
    )
