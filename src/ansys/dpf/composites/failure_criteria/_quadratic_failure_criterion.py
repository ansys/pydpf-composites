"""Base class for quadratic failure criterion."""

from ._failure_criterion_base import FailureCriterionBase

_DOC_WF = "Weighting factor of this failure criterion."
_DOC_DIM = "Specifies which formulation of the failure criterion is used."


class QuadraticFailureCriterion(FailureCriterionBase):
    """Base class for quadratic failure criteria.

    Such as Tsai-Wu, Tsai-Hill and Hoffman.
    """

    def __init__(self, *, name: str, active: bool, wf: float, dim: int):
        """Do not use directly. Base class for quadratic failure criteria."""
        super().__init__(name=name, active=active)

        self.dim = dim
        self.wf = wf

    def _get_wf(self) -> float:
        return self._wf

    def _set_wf(self, value: float) -> None:
        self._wf = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3."
            )

    wf = property(_get_wf, _set_wf, doc=_DOC_WF)
    dim = property(_get_dim, _set_dim, doc=_DOC_DIM)
