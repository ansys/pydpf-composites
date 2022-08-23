"""Hoffman Failure Criterion."""

from .quadratic_failure_criterion import QuadraticFailureCriterion


class HoffmanCriterion(QuadraticFailureCriterion):
    """
    Defines the Hoffman failure criterion for orthotropic reinforced materials.
    """

    def __init__(self, active: bool = True, wf: float = 1.0, dim: int = 2):

        super().__init__(name="Hoffman", active=active, dim=dim, wf=wf)
