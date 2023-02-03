"""Tsai-Hill failure criterion."""

from ._quadratic_failure_criterion import _DOC_DIM, _DOC_WF, QuadraticFailureCriterion


class TsaiHillCriterion(QuadraticFailureCriterion):
    """Tsai Hill Criterion."""

    __doc__ = f"""Defines the Tsai-Hill failure criterion for orthotropic reinforced materials.

    Parameters
    ----------
    wf:
        {_DOC_WF}
    dim:
        {_DOC_DIM}
    """

    def __init__(self, *, active: bool = True, wf: float = 1.0, dim: int = 2):
        """Create a Tsai-Hill failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Tsai Hill", active=active, dim=dim, wf=wf)
