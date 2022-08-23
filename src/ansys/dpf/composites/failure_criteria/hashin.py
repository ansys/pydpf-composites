from .failure_criterion_base import FailureCriterionBase

ATTRS_HASHIN = ["hf", "hm", "hd", "dim", "wf_hf", "wf_hm", "wf_hd"]


class HashinCriterion(FailureCriterionBase):
    """
    Defines the Hashin failure criterion for uni-directional orthotropic reinforced materials.
    """

    def __init__(
        self,
        hf: bool = True,
        hm: bool = True,
        hd: bool = False,
        dim: int = 2,
        wf_hf: float = 1.0,
        wf_hm: float = 1.0,
        wf_hd: float = 1.0,
    ):

        super().__init__(name="Hashin", active=True)

        for attr in ATTRS_HASHIN:
            setattr(self, attr, eval(attr))

    def _get_hf(self) -> bool:
        return self._hf

    def _set_hf(self, value: bool):
        self._hf = value

    def _get_hm(self) -> bool:
        return self._hm

    def _set_hm(self, value: bool):
        self._hm = value

    def _get_hd(self) -> bool:
        return self._hd

    def _set_hd(self, value: bool):
        self._hd = value

    def _get_dim(self) -> int:
        return self._dim

    def _set_dim(self, value: int):
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(
                f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3."
            )

    def _get_wf_hf(self) -> float:
        return self._wf_hf

    def _set_wf_hf(self, value: float):
        self._wf_hf = value

    def _get_wf_hm(self) -> float:
        return self._wf_hm

    def _set_wf_hm(self, value: float):
        self._wf_hm = value

    def _get_wf_hd(self) -> float:
        return self._wf_hd

    def _set_wf_hd(self, value: float):
        self._wf_hd = value

    hf = property(_get_hf, _set_hf, doc="Activates the failure evaluation regarding fiber failure.")
    hm = property(
        _get_hm, _set_hm, doc="Activates the failure evaluation regarding matrix failure."
    )
    hd = property(
        _get_hd,
        _set_hd,
        doc="Activates the failure evaluation regarding delamination if dim is equal to 3.",
    )
    dim = property(
        _get_dim,
        _set_dim,
        doc="Whether the 2D or 3D formulation of the criterion is used. The latter one also "
        "supports the failure mode delamination.",
    )
    wf_hf = property(_get_wf_hf, _set_wf_hf, doc="Weighting factor of the fiber failure (hf) mode.")
    wf_hm = property(
        _get_wf_hm, _set_wf_hm, doc="Weighting factor of the matrix failure (hm) mode."
    )
    wf_hd = property(_get_wf_hd, _set_wf_hd, doc="Weighting factor of the delamination (hd) mode.")
