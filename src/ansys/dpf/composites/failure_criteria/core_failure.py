"""Core Failure Criterion."""
import inspect

from .failure_criterion_base import FailureCriterionBase


class CoreFailureCriterion(FailureCriterionBase):
    """Defines the core shear failure criterion for core materials like foam and honeycomb."""

    def __init__(self, *, include_ins: bool = False, wf: float = 1.0):
        """Construct a core failure criterion.

        :param include_ins: whether to include interlaminar normals stresses or not.
        :param wf: weighting factor.
        """
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

    include_ins = property(
        _get_include_ins,
        _set_include_ins,
        doc="Activate this option to enable the formulation which "
        "considers interlaminar normal stresses.",
    )
    wf = property(_get_wf, _set_wf, doc="Weighting factor of the failure mode (cs).")


ATTRS_CORE_FAILURE = inspect.signature(CoreFailureCriterion).parameters.keys()
