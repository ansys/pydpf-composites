"""
Defines the MaxStrain failure criterion
"""

from failure_criteion_base import FailureCriterionBase

ATTRS_MAX_STRAIN = ["e1_active", "e2_active", "e3_active", "e12_active", "e13_active", "e23_active",
                    "wf_e1", "wf_e2", "wf_e3", "wf_e12", "wf_e13", "wf_e23",
                    "force_global_limits",
                    "e1t", "e1c", "e2t", "e2c", "e3t", "e3c", "e12", "e23", "e13"]

class MaxStrainCriterion(FailureCriterionBase):
    """
    Defines the Maximum Strain failure criterion for orthotropic reinforced materials.
    """

    def __init__(self,
                 e1_active: bool = True,
                 e2_active: bool = True,
                 e3_active: bool = False,
                 e12_active: bool = True,
                 e13_active: bool = False,
                 e23_active: bool = False,
                 wf_e1: float = 1.,
                 wf_e2: float = 1.,
                 wf_e3: float = 1.,
                 wf_e12: float = 1.,
                 wf_e13: float = 1.,
                 wf_e23: float = 1.,
                 force_global_limits: bool = False,
                 e1t: float = 0.,
                 e1c: float = 0.,
                 e2t: float = 0.,
                 e2c: float = 0.,
                 e3t: float = 0.,
                 e3c: float = 0.,
                 e12: float = 0.,
                 e13: float = 0.,
                 e23: float = 0.
                 ):
        
        super().__init__(name="Max Strain", active=True)

        for attr in ATTRS_MAX_STRAIN:
            setattr(self, attr, eval(attr))

    def _get_e1_active(self) -> bool:
        return self._e1_active
    def _set_e1_active(self, value: bool):
        self._e1_active = value

    def _get_e2_active(self) -> bool:
        return self._e2_active
    def _set_e2_active(self, value: bool):
        self._e2_active = value

    def _get_e3_active(self) -> bool:
        return self._e3_active
    def _set_e3_active(self, value: bool):
        self._e3_active = value

    def _get_e12_active(self) -> bool:
        return self._e12_active
    def _set_e12_active(self, value: bool):
        self._e12_active = value

    def _get_e13_active(self) -> bool:
        return self._e13_active
    def _set_e13_active(self, value: bool):
        self._e13_active = value

    def _get_e23_active(self) -> bool:
        return self._e23_active
    def _set_e23_active(self, value: bool):
        self._e23_active = value

    def _get_wf_e1(self) -> float:
        return self._wf_e1
    def _set_wf_e1(self, value: float):
        self._wf_e1 = value

    def _get_wf_e2(self) -> float:
        return self._wf_e2
    def _set_wf_e2(self, value: float):
        self._wf_e2 = value

    def _get_wf_e3(self) -> float:
        return self._wf_e3
    def _set_wf_e3(self, value: float):
        self._wf_e3 = value

    def _get_wf_e12(self) -> float:
        return self._wf_e12
    def _set_wf_e12(self, value: float):
        self._wf_e12 = value

    def _get_wf_e13(self) -> float:
        return self._wf_e13
    def _set_wf_e13(self, value: float):
        self._wf_e13 = value

    def _get_wf_e23(self) -> float:
        return self._wf_e23
    def _set_wf_e23(self, value: float):
        self._wf_e23 = value

    def _get_force_global_limits(self) -> bool:
        return self._force_global_limits
    def _set_force_global_limits(self, value: bool):
        self._force_global_limits = value

    def _get_e1t(self) -> float:
        return self._e1t
    def _set_e1t(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit e1t cannot be negative.")
        self._e1t = value

    def _get_e1c(self) -> float:
        return self._e1c
    def _set_e1c(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit e1c cannot be positive.")
        self._e1c = value

    def _get_e2t(self) -> float:
        return self._e2t
    def _set_e2t(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit e2t cannot be negative.")
        self._e2t = value

    def _get_e2c(self) -> float:
        return self._e2c
    def _set_e2c(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit e2c cannot be positive.")
        self._e2c = value

    def _get_e3t(self) -> float:
        return self._e3t
    def _set_e3t(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit e3t cannot be negative.")
        self._e3t = value

    def _get_e3c(self) -> float:
        return self._e3c
    def _set_e3c(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit e3c cannot be positive.")
        self._e3c = value

    def _get_e12(self) -> float:
        return self._e12
    def _set_e12(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit e12 cannot be negative.")
        self._e12 = value

    def _get_e13(self) -> float:
        return self._e13
    def _set_e13(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit e13 cannot be negative.")
        self._e13 = value

    def _get_e23(self) -> float:
        return self._e23
    def _set_e23(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit e23 cannot be negative.")
        self._e23 = value

    e1_active = property(_get_e1_active, _set_e1_active,
                         doc="Activates the failure evaluation regarding the strain in the material 1 direction.")
    e2_active = property(_get_e2_active, _set_e2_active,
                         doc="Activates the failure evaluation regarding the strain in the material 2 direction.")
    e3_active = property(_get_e3_active, _set_e3_active,
                         doc="Activates the failure evaluation regarding the strain in the material 3 direction (out-of-plane).")
    e12_active = property(_get_e12_active, _set_e12_active,
                         doc="Activates the failure evaluation regarding the in-plane shear strain e12.")
    e13_active = property(_get_e13_active, _set_e13_active,
                          doc="Activates the failure evaluation regarding the interlaminar shear strain e13.")
    e23_active = property(_get_e23_active, _set_e23_active,
                          doc="Activates the failure evaluation regarding the interlaminar shear strain e23.")

    wf_e1 = property(_get_wf_e1, _set_wf_e1,
                     doc="Weighting factor of the failure mode e1.")
    wf_e2 = property(_get_wf_e2, _set_wf_e2,
                     doc="Weighting factor of the failure mode e2.")
    wf_e3 = property(_get_wf_e3, _set_wf_e3,
                     doc="Weighting factor of the failure mode e3.")
    wf_e12 = property(_get_wf_e12, _set_wf_e12,
                     doc="Weighting factor of the failure mode e12.")
    wf_e13 = property(_get_wf_e13, _set_wf_e13,
                     doc="Weighting factor of the failure mode e13.")
    wf_e23 = property(_get_wf_e23, _set_wf_e23,
                     doc="Weighting factor of the failure mode e23.")

    force_global_limits = property(_get_force_global_limits, _set_force_global_limits,
                          doc="Whether to use global limits instead of strain limits of the materials.")

    e1t = property(_get_e1t, _set_e1t,
                      doc="Global tensile strain limit in material direction 1.")
    e1c = property(_get_e1c, _set_e1c,
                   doc="Global compressive strain limit in material direction 1.")
    e2t = property(_get_e2t, _set_e2t,
                   doc="Global tensile strain limit in material direction 2.")
    e2c = property(_get_e2c, _set_e2c,
                   doc="Global compressive strain limit in material direction 2.")
    e3t = property(_get_e3t, _set_e3t,
                   doc="Global _set_e2c strain limit in material direction 3.")
    e3c = property(_get_e3c, _set_e3c,
                   doc="Global compressive strain limit in material direction 3.")
    e12 = property(_get_e12, _set_e12,
                   doc="Global strain limit in material direction 12.")
    e13 = property(_get_e13, _set_e13,
                   doc="Global strain limit in material direction 13.")
    e23 = property(_get_e23, _set_e23,
                   doc="Global strain limit in material direction 23.")
