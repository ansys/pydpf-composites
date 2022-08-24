"""Von Mises Criterion"""

from .failure_criterion_base import FailureCriterionBase

ATTRS_VON_MISES = ["vme", "vms", "wf_vme", "wf_vms", "iss", "ins"]


class VonMisesCriterion(FailureCriterionBase):
    def __init__(
        self,
        vme: bool = True,
        vms: bool = True,
        wf_vme: float = 1.0,
        wf_vms: float = 1.0,
        iss: bool = True,
        ins: bool = False,
    ):
        """Defines the von Mises criterion for isotropic materials."""

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

    def _get_iss(self) -> bool:
        return self._iss

    def _set_iss(self, value: bool) -> None:
        self._iss = value

    def _get_ins(self) -> bool:
        return self._ins

    def _set_ins(self, value: bool) -> None:
        self._ins = value

    vme = property(_get_vme, _set_vme, doc="Activates the von Mises strain criterion.")
    vms = property(_get_vms, _set_vms, doc="Activates the von Mises stress criterion.")
    wf_vme = property(_get_wf_vme, _set_wf_vme, doc="Weighting factor of strain criterion (vme).")
    wf_vms = property(
        _get_wf_vms, _set_wf_vms, doc="Weighting factor of the stress criterion (vms)."
    )
    iss = property(
        _get_iss,
        _set_iss,
        doc="Whether to consider the interlaminar shear stresses in the stress criterion.",
    )
    ins = property(
        _get_ins,
        _set_ins,
        doc="Whether to consider the interlaminar normal stress in the stress criterion.",
    )
