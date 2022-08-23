"""Face Sheet Wrinkling Criterion for sandwich structures"""

from .failure_criterion_base import FailureCriterionBase

ATTRS_WRINKLING = ["homogeneous_core_coeff", "honeycomb_core_coeff", "wf"]


class FaceSheetWrinklingCriterion(FailureCriterionBase):
    """
    Defines the face sheet wrinkling failure criterion for sandwiches (laminate with cores)
    """

    def __init__(
        self,
        homogeneous_core_coeff: float = 0.5,
        honeycomb_core_coeff: float = 0.33,
        wf: float = 1.0,
    ):

        super().__init__(name="Face Sheet Wrinkling", active=True)

        for attr in ATTRS_WRINKLING:
            setattr(self, attr, eval(attr))

    def _get_homogeneous_core_coeff(self) -> float:
        return self._homogeneous_core_coeff

    def _set_homogeneous_core_coeff(self, value: float):
        if value > 0:
            self._homogeneous_core_coeff = value
        else:
            raise ValueError("Homogeneous core coefficient must be greater than 0.")

    def _get_honeycomb_core_coeff(self) -> float:
        return self._honeycomb_core_coeff

    def _set_honeycomb_core_coeff(self, value: float):
        if value > 0:
            self._honeycomb_core_coeff = value
        else:
            raise ValueError("Honeycomb core coefficient must be greater than 0.")

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float):
        self._wf = value

    wf = property(_get_wf, _set_wf, doc="Weighting factor of the failure mode (wb or wt).")
    homogeneous_core_coeff = property(
        _get_homogeneous_core_coeff,
        _set_homogeneous_core_coeff,
        doc="Wrinkling coefficient (reduction factor) for homogeneous core materials. "
        "Default is 0.5",
    )
    honeycomb_core_coeff = property(
        _get_honeycomb_core_coeff,
        _set_honeycomb_core_coeff,
        doc="Wrinkling coefficient (reduction factor) for honeycombs. Default is 0.33.",
    )
