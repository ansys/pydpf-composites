from .failure_criterion_base import FailureCriterionBase

ATTRS_SHEAR_CRIMPING = ["kc", "kf", "wf"]


class ShearCrimpingCriterion(FailureCriterionBase):
    """
    Defines the shear crimping failure criterion for sandwich structures (laminate with cores)
    """

    def __init__(self, kc: float = 1.0, kf: float = 0.0, wf: float = 1.0):

        super().__init__(name="Shear Crimping", active=True)

        for attr in ATTRS_SHEAR_CRIMPING:
            setattr(self, attr, eval(attr))

    def _get_kc(self) -> float:
        return self._kc

    def _set_kc(self, value: float):
        self._kc = value

    def _get_kf(self) -> float:
        return self._kf

    def _set_kf(self, value: float):
        self._kf = value

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float):
        self._wf = value

    wf = property(_get_wf, _set_wf, doc="Weighting factor of the failure mode (wb or wt).")
    kc = property(
        _get_kc,
        _set_kc,
        doc="Weighting factor of the core material for evaluation of the maximum allowable load. "
        "Default is 1.",
    )
    kf = property(
        _get_kf,
        _set_kf,
        doc="Weighting factor of the face sheets for evaluation of the maximum allowable load. "
        "Default is 0 so the face sheet do not contribute to the allowable load. Valid for thin "
        "face sheets.",
    )
