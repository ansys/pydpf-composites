"""Shear Crimping Failure Criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_WF = "Weighting factor of the failure mode (wb or wt)."
_DOC_KC = (
    "Weighting factor of the core material for evaluation of the "
    "maximum allowable load. The default is ``1``."
)
_DOC_KF = (
    "Weighting factor of the face sheets for evaluation of the maximum allowable load. "
    "The default is ``0`` so the face sheet does not contribute to the allowable load. "
    "This property is valid for thin face sheets."
)


class ShearCrimpingCriterion(FailureCriterionBase):
    """Shear Crimping Criterion."""

    __doc__ = f"""Defines the shear crimping failure criterion for sandwich structures.

    Parameters
    ----------
    kc:
        {_DOC_KC}
    kf:
        {_DOC_KF}
    wf:
        {_DOC_WF}
    """

    def __init__(self, *, kc: float = 1.0, kf: float = 0.0, wf: float = 1.0):
        """Create a shear crimping failure criterion for sandwich structures.

        A laminate is classified as sandwich if it has at least one core material.
        A honeycomb is an example.
        """
        super().__init__(name="Shear Crimping", active=True)

        for attr in ATTRS_SHEAR_CRIMPING:
            setattr(self, attr, eval(attr))

    def _get_kc(self) -> float:
        return self._kc

    def _set_kc(self, value: float) -> None:
        self._kc = value

    def _get_kf(self) -> float:
        return self._kf

    def _set_kf(self, value: float) -> None:
        self._kf = value

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    wf = property(_get_wf, _set_wf, doc=_DOC_WF)
    kc = property(_get_kc, _set_kc, doc=_DOC_KC)
    kf = property(_get_kf, _set_kf, doc=_DOC_KF)


ATTRS_SHEAR_CRIMPING = inspect.signature(ShearCrimpingCriterion).parameters.keys()
