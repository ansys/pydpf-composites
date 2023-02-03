"""Hoffman failure criterion."""

from ._quadratic_failure_criterion import _DOC_DIM, _DOC_WF, QuadraticFailureCriterion


class HoffmanCriterion(QuadraticFailureCriterion):
    """Hoffman Criterion."""

    __doc__ = f"""Defines the Hoffman failure criterion for orthotropic reinforced materials.

    Parameters
    ----------
    wf:
        {_DOC_WF}
    dim:
        {_DOC_DIM}
    """

    def __init__(self, *, active: bool = True, wf: float = 1.0, dim: int = 2):
        """Create a Hoffman failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Hoffman", active=active, dim=dim, wf=wf)
