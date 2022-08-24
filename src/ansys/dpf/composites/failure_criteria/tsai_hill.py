"""Tsai-Hill Failure Criterion."""

from .quadratic_failure_criterion import QuadraticFailureCriterion


class TsaiHillCriterion(QuadraticFailureCriterion):
    """Defines the Tsai-Hill failure criterion for orthotropic reinforced materials."""

    def __init__(self, active: bool = True, wf: float = 1.0, dim: int = 2):
        """Create a Tsai-Hill failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Tsai Hill", active=active, dim=dim, wf=wf)
