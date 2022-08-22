
from .failure_criterion_base import FailureCriterionBase
import math

ATTRS_CUNTZE = ["cfc", "cft", "cma", "cmb", "cmc", "dim",
              "wf_cfc", "wf_cft", "wf_cma", "wf_cmb", "wf_cmc",
              "b21", "b32", "fracture_plane_angle", "mode_interaction_coeff"]

class CuntzeCriterion(FailureCriterionBase):
    """
    Defines the LaRC failure criterion for uni-directional orthotropic reinforced materials.
    """

    def __init__(self,
                 cfc: bool = True,
                 cft: bool = True,
                 cma: bool = True,
                 cmb: bool = True,
                 cmc: bool = True,
                 dim: int = 2,
                 wf_cfc: float = 1.,
                 wf_cft: float = 1.,
                 wf_cma: float = 1.,
                 wf_cmb: float = 1.,
                 wf_cmc: float = 1.,
                 b21: float = 0.2,
                 b32: float = 1.3805,
                 fracture_plane_angle: float = 53.,
                 mode_interaction_coeff: float = 2.6
                 ):

        super().__init__(name="Cuntze", active=True)

        for attr in ATTRS_CUNTZE:
            setattr(self, attr, eval(attr))

    def _get_cfc(self) -> bool:
        return self._cfc
    def _set_cfc(self, value: bool):
        self._cfc = value

    def _get_cft(self) -> bool:
        return self._cft
    def _set_cft(self, value: bool):
        self._cft = value

    def _get_cma(self) -> bool:
        return self._cma
    def _set_cma(self, value: bool):
        self._cma = value

    def _get_cmb(self) -> bool:
        return self._cmb
    def _set_cmb(self, value: bool):
        self._cmb = value

    def _get_cmc(self) -> bool:
        return self._cmc
    def _set_cmc(self, value: bool):
        self._cmc = value

    def _get_dim(self) -> int:
        return self._dim
    def _set_dim(self, value: int):
        if value in [2, 3]:
            self._dim = value
        else:
            raise AttributeError(f"Dimension of {self.name} cannot be set to {value}. Allowed are 2 or 3.")

    def _get_wf_cfc(self) -> float:
        return self._wf_cfc
    def _set_wf_cfc(self, value: float):
        self._wf_cfc = value

    def _get_wf_cft(self) -> float:
        return self._wf_cft
    def _set_wf_cft(self, value: float):
        self._wf_cft = value

    def _get_wf_cma(self) -> float:
        return self._wf_cma
    def _set_wf_cma(self, value: float):
        self._wf_cma = value

    def _get_wf_cmb(self) -> float:
        return self._wf_cmb
    def _set_wf_cmb(self, value: float):
        self._wf_cmb = value

    def _get_wf_cmc(self) -> float:
        return self._wf_cmc
    def _set_wf_cmc(self, value: float):
        self._wf_cmc = value

    def _get_b21(self) -> float:
        return self._b21
    def _set_b21(self, value: float):
        self._b21 = value

    def _get_b32(self) -> float:
        return self._b32
    def _set_b32(self, value: float):
        if value >= 1.0:
            self._fracture_plane_angle = (
                math.acos(1.0 / value - 1.0) / 2.0 * 180.0 / math.pi
            )
            self._b32 = value
        else:
            raise ValueError("Out-of-plane friction coefficient b32 must be 1 or above.")

    def _get_fracture_plane_angle(self) -> float:
        return self._fracture_plane_angle
    def _set_fracture_plane_angle(self, value: float):
        if value > 45.:
            self._b32 = 1.0 / (1.0 + math.cos(2.0 * math.pi * value / 180.0))
            self._fracture_plane_angle = value
        else:
            raise ValueError("Fracture plane angle must be above 45 degrees.")

    def _get_mode_interaction_coeff(self) -> float:
        return self._mode_interaction_coeff
    def _set_mode_interaction_coeff(self, value: float):
        self._mode_interaction_coeff = value

    cfc = property(_get_cfc, _set_cfc,
                         doc="Activates the failure evaluation regarding compression in fiber direction.")
    cft = property(_get_cft, _set_cft,
                         doc="Activates the failure evaluation regarding tension in fiber direction.")
    cma = property(_get_cma, _set_cma,
                   doc="Activates the failure evaluation of matrix due to tension.")
    cmb = property(_get_cmb, _set_cmb,
                   doc="Activates the failure evaluation of matrix due to compression.")
    cmc = property(_get_cmc, _set_cmc,
                   doc="Activates the failure evaluation of matrix due to compression / shear.")

    dim = property(_get_dim, _set_dim,
                         doc="Whether the 2D or 3D formulation of the criterion is used.")
    wf_cfc = property(_get_wf_cfc, _set_wf_cfc,
                          doc="Weighting factor of fiber failure due to compression (cfc).")
    wf_cft = property(_get_wf_cft, _set_wf_cft,
                      doc="Weighting factor of fiber failure due to tension (cft).")
    wf_cma = property(_get_wf_cma, _set_wf_cma,
                      doc="Weighting factor of matrix failure due to tension (cma).")
    wf_cmb = property(_get_wf_cmb, _set_wf_cmb,
                      doc="Weighting factor of matrix failure due to compression (cmb).")
    wf_cmc = property(_get_wf_cmc, _set_wf_cmc,
                      doc="Weighting factor of matrix failure due to compression / shear (cmc).")

    b21 = property(_get_b21, _set_b21,
                      doc="In-plane shear friction coefficient. Default is 0.2.")
    b32 = property(_get_b32, _set_b32,
                      doc="Out-of-plane shear friction coefficient. Default is 1.3805. Depends on the fracture "
                          "plane angle.")
    mode_interaction_coeff = property(_get_mode_interaction_coeff, _set_mode_interaction_coeff,
                      doc="Mode interaction coefficient. Default is 2.6.")
    fracture_plane_angle = property(_get_fracture_plane_angle, _set_fracture_plane_angle,
                      doc="Fracture plane angle. Default is 53 degree. Must be > 45. Depends on the out-of-plane "
                          "shear friction coefficient.")
