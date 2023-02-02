"""Core failure criterion."""
import inspect

from ._failure_criterion_base import FailureCriterionBase

_DOC_INCLUDE_INS = (
    "Whether to activate the formulation that considers interlaminar normal stresses."
)

_DOC_WF = "Weighting factor of the failure mode (cs)."


class CoreFailureCriterion(FailureCriterionBase):
    """Defines the core failure criterion."""

    __doc__ = f"""Defines the core shear failure criterion for
    core materials like foam and honeycomb.

    Parameters
    ----------
    include_ins:
        {_DOC_INCLUDE_INS}
    wf:
        {_DOC_WF}
    """

    def __init__(self, *, include_ins: bool = False, wf: float = 1.0):
        """Create a core failure criterion."""
        super().__init__(name="Core Failure", active=True)

        for attr in ATTRS_CORE_FAILURE:
            setattr(self, attr, eval(attr))

    def _get_include_ins(self) -> bool:
        return self._include_ins

    def _set_include_ins(self, value: bool) -> None:
        self._include_ins = value

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    include_ins = property(_get_include_ins, _set_include_ins, doc=_DOC_INCLUDE_INS)
    wf = property(_get_wf, _set_wf, doc=_DOC_WF)


ATTRS_CORE_FAILURE = inspect.signature(CoreFailureCriterion).parameters.keys()
