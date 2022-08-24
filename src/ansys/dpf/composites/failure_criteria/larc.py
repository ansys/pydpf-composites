"""LaRC Failure Criterion."""

from .failure_criterion_base import FailureCriterionBase

ATTRS_LARC = ["lft", "lfc", "lmt", "lmc", "dim", "wf_lft", "wf_lfc", "wf_lmt", "wf_lmc"]


class LaRCCriterion(FailureCriterionBase):
    """Defines the LaRC failure criterion for UD reinforced materials."""

    def __init__(
        self,
        lft: bool = True,
        lfc: bool = True,
        lmt: bool = True,
        lmc: bool = True,
        dim: int = 2,
        wf_lft: float = 1.0,
        wf_lfc: float = 1.0,
        wf_lmt: float = 1.0,
        wf_lmc: float = 1.0,
    ):
        """Create a LaRC failure criterion for uni-directional reinforced materials."""
        super().__init__(name="LaRC", active=True)

        for attr in ATTRS_LARC:
            setattr(self, attr, eval(attr))

    def _get_lfc(self) -> bool:
        return self._lfc

    def _set_lfc(self, value: bool) -> None:
        self._lfc = value

    def _get_lft(self) -> bool:
        return self._lft

    def _set_lft(self, value: bool) -> None:
        self._lft = value

    def _get_lmc(self) -> bool:
        return self._lmc

    def _set_lmc(self, value: bool) -> None:
        self._lmc = value

    def _get_lmt(self) -> bool:
        return self._lmt

    def _set_lmt(self, value: bool) -> None:
        self._lmt = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int) -> None:
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3 for "
                f" LaRC03 and LaRC04 respectively."
            )

    def _get_wf_lfc(self) -> float:
        return self._wf_lfc

    def _set_wf_lfc(self, value: float) -> None:
        self._wf_lfc = value

    def _get_wf_lft(self) -> float:
        return self._wf_lft

    def _set_wf_lft(self, value: float) -> None:
        self._wf_lft = value

    def _get_wf_lmc(self) -> float:
        return self._wf_lmc

    def _set_wf_lmc(self, value: float) -> None:
        self._wf_lmc = value

    def _get_wf_lmt(self) -> float:
        return self._wf_lmt

    def _set_wf_lmt(self, value: float) -> None:
        self._wf_lmt = value

    lfc = property(
        _get_lfc,
        _set_lfc,
        doc="Activates the failure evaluation regarding compression in fiber direction.",
    )
    lft = property(
        _get_lft,
        _set_lft,
        doc="Activates the failure evaluation regarding tension in fiber direction.",
    )
    lmc = property(
        _get_lmc, _set_lmc, doc="Activates the failure evaluation of matrix due to compression."
    )
    lmt = property(
        _get_lmt, _set_lmt, doc="Activates the failure evaluation of matrix due to tension."
    )

    dim = property(
        _get_dim,
        _set_dim,
        doc="Whether the 2D or 3D formulation of the criterion is used. 2D is equivalent to "
        "LaRC03, and 3D to LaRC04.",
    )
    wf_lfc = property(
        _get_wf_lfc, _set_wf_lfc, doc="Weighting factor of fiber failure due to compression (lfc)."
    )
    wf_lft = property(
        _get_wf_lft, _set_wf_lft, doc="Weighting factor of fiber failure due to tension (lft)."
    )
    wf_lmc = property(
        _get_wf_lmc, _set_wf_lmc, doc="Weighting factor of matrix failure due to compression (lmc)."
    )
    wf_lmt = property(
        _get_wf_lmt, _set_wf_lmt, doc="Weighting factor of matrix failure due to tension (lmt)."
    )
