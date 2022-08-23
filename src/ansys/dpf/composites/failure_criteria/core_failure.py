"""Core Failure Criterion"""

from .failure_criterion_base import FailureCriterionBase

ATTRS_CORE_FAILURE = ["include_ins", "wf"]


class CoreFailureCriterion(FailureCriterionBase):
    """
    Defines the core shear failure criterion for core materials like foam and honeycomb.
    """

    def __init__(self, include_ins: bool = False, wf: float = 1.0):

        super().__init__(name="Core Failure", active=True)

        for attr in ATTRS_CORE_FAILURE:
            setattr(self, attr, eval(attr))

    def _get_include_ins(self) -> bool:
        return self._include_ins

    def _set_include_ins(self, value: bool):
        self._include_ins = value

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float):
        self._wf = value

    include_ins = property(
        _get_include_ins,
        _set_include_ins,
        doc="Activate this option to enable the formulation which "
        "considers interlaminar normal stresses.",
    )
    wf = property(_get_wf, _set_wf, doc="Weighting factor of the failure mode (cs).")
