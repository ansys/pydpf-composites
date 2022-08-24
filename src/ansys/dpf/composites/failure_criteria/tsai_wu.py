"""Tsai-Wu Failure Criterion."""

from .quadratic_failure_criterion import QuadraticFailureCriterion


class TsaiWuCriterion(QuadraticFailureCriterion):
    """Defines the Tsai-Wu failure criterion for orthotropic reinforced materials."""

    def __init__(self, active: bool = True, wf: float = 1.0, dim: int = 2):
        """Create a Tsai-Wu failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Tsai Wu", active=active, dim=dim, wf=wf)
