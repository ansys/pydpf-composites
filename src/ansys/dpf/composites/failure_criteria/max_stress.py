"""
Defines the MaxStress failure criterion
"""

from .failure_criterion_base import FailureCriterionBase

ATTRS_MAX_STRESS = ["s1_active", "s2_active", "s3_active", "s12_active", "s13_active", "s23_active",
                    "wf_s1", "wf_s2", "wf_s3", "wf_s12", "wf_s13", "wf_s23"]

class MaxStressCriterion(FailureCriterionBase):
    """
    Defines the Maximum Stress failure criterion for orthotropic reinforced materials.
    """

    def __init__(self,
                 s1_active: bool = True,
                 s2_active: bool = True,
                 s3_active: bool = False,
                 s12_active: bool = True,
                 s13_active: bool = False,
                 s23_active: bool = False,
                 wf_s1: float = 1.,
                 wf_s2: float = 1.,
                 wf_s3: float = 1.,
                 wf_s12: float = 1.,
                 wf_s13: float = 1.,
                 wf_s23: float = 1.
                 ):

        super().__init__(name="Max Stress", active=True)

        for attr in ATTRS_MAX_STRESS:
            setattr(self, attr, eval(attr))

    def _get_s1_active(self) -> bool:
        return self._s1_active
    def _set_s1_active(self, value: bool):
        self._s1_active = value

    def _get_s2_active(self) -> bool:
        return self._s2_active
    def _set_s2_active(self, value: bool):
        self._s2_active = value

    def _get_s3_active(self) -> bool:
        return self._s3_active
    def _set_s3_active(self, value: bool):
        self._s3_active = value

    def _get_s12_active(self) -> bool:
        return self._s12_active
    def _set_s12_active(self, value: bool):
        self._s12_active = value

    def _get_s13_active(self) -> bool:
        return self._s13_active
    def _set_s13_active(self, value: bool):
        self._s13_active = value

    def _get_s23_active(self) -> bool:
        return self._s23_active
    def _set_s23_active(self, value: bool):
        self._s23_active = value

    def _get_wf_s1(self) -> float:
        return self._wf_s1
    def _set_wf_s1(self, value: float):
        self._wf_s1 = value

    def _get_wf_s2(self) -> float:
        return self._wf_s2
    def _set_wf_s2(self, value: float):
        self._wf_s2 = value

    def _get_wf_s3(self) -> float:
        return self._wf_s3
    def _set_wf_s3(self, value: float):
        self._wf_s3 = value

    def _get_wf_s12(self) -> float:
        return self._wf_s12
    def _set_wf_s12(self, value: float):
        self._wf_s12 = value

    def _get_wf_s13(self) -> float:
        return self._wf_s13
    def _set_wf_s13(self, value: float):
        self._wf_s13 = value

    def _get_wf_s23(self) -> float:
        return self._wf_s23
    def _set_wf_s23(self, value: float):
        self._wf_s23 = value

    s1_active = property(_get_s1_active, _set_s1_active,
                         doc="Activates the failure evaluation regarding the stress in the material 1 direction.")
    s2_active = property(_get_s2_active, _set_s2_active,
                         doc="Activates the failure evaluation regarding the stress in the material 2 direction.")
    s3_active = property(_get_s3_active, _set_s3_active,
                         doc="Activates the failure evaluation regarding the stress in the material 3 direction (out-of-plane).")
    s12_active = property(_get_s12_active, _set_s12_active,
                         doc="Activates the failure evaluation regarding the in-plane shear stress s12.")
    s13_active = property(_get_s13_active, _set_s13_active,
                          doc="Activates the failure evaluation regarding the interlaminar shear stress s13.")
    s23_active = property(_get_s23_active, _set_s23_active,
                          doc="Activates the failure evaluation regarding the interlaminar shear stress s23.")

    wf_s1 = property(_get_wf_s1, _set_wf_s1,
                     doc="Weighting factor of the failure mode s1.")
    wf_s2 = property(_get_wf_s2, _set_wf_s2,
                     doc="Weighting factor of the failure mode s2.")
    wf_s3 = property(_get_wf_s3, _set_wf_s3,
                     doc="Weighting factor of the failure mode s3.")
    wf_s12 = property(_get_wf_s12, _set_wf_s12,
                     doc="Weighting factor of the failure mode s12.")
    wf_s13 = property(_get_wf_s13, _set_wf_s13,
                     doc="Weighting factor of the failure mode s13.")
    wf_s23 = property(_get_wf_s23, _set_wf_s23,
                     doc="Weighting factor of the failure mode s23.")
