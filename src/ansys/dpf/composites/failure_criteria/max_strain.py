"""
Defines the MaxStrain failure criterion
"""

from .failure_criterion_base import FailureCriterionBase

ATTRS_MAX_STRAIN = ["e1", "e2", "e3", "e12", "e13", "e23",
                    "wf_e1", "wf_e2", "wf_e3", "wf_e12", "wf_e13", "wf_e23",
                    "force_global_strain_limits",
                    "eXt", "eXc", "eYt", "eYc", "eZt", "eZc", "eSxy", "eSyz", "eSxz"]

class MaxStrainCriterion(FailureCriterionBase):
    """
    Defines the Maximum Strain failure criterion for orthotropic reinforced materials.
    """

    def __init__(self,
                 e1: bool = True,
                 e2: bool = True,
                 e3: bool = False,
                 e12: bool = True,
                 e13: bool = False,
                 e23: bool = False,
                 wf_e1: float = 1.,
                 wf_e2: float = 1.,
                 wf_e3: float = 1.,
                 wf_e12: float = 1.,
                 wf_e13: float = 1.,
                 wf_e23: float = 1.,
                 force_global_strain_limits: bool = False,
                 eXt: float = 0.,
                 eXc: float = 0.,
                 eYt: float = 0.,
                 eYc: float = 0.,
                 eZt: float = 0.,
                 eZc: float = 0.,
                 eSxy: float = 0.,
                 eSxz: float = 0.,
                 eSyz: float = 0.
                 ):
        
        super().__init__(name="Max Strain", active=True)

        for attr in ATTRS_MAX_STRAIN:
            setattr(self, attr, eval(attr))

    def _get_e1(self) -> bool:
        return self._e1
    def _set_e1(self, value: bool):
        self._e1 = value

    def _get_e2(self) -> bool:
        return self._e2
    def _set_e2(self, value: bool):
        self._e2 = value

    def _get_e3(self) -> bool:
        return self._e3
    def _set_e3(self, value: bool):
        self._e3 = value

    def _get_e12(self) -> bool:
        return self._e12
    def _set_e12(self, value: bool):
        self._e12 = value

    def _get_e13(self) -> bool:
        return self._e13
    def _set_e13(self, value: bool):
        self._e13 = value

    def _get_e23(self) -> bool:
        return self._e23
    def _set_e23(self, value: bool):
        self._e23 = value

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

    def _get_force_global_strain_limits(self) -> bool:
        return self._force_global_strain_limits
    def _set_force_global_strain_limits(self, value: bool):
        self._force_global_strain_limits = value

    def _get_eXt(self) -> float:
        return self._eXt
    def _set_eXt(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit eXt cannot be negative.")
        self._eXt = value

    def _get_eXc(self) -> float:
        return self._eXc
    def _set_eXc(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit eXc cannot be positive.")
        self._eXc = value

    def _get_eYt(self) -> float:
        return self._eYt
    def _set_eYt(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit eYt cannot be negative.")
        self._eYt = value

    def _get_eYc(self) -> float:
        return self._eYc
    def _set_eYc(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit eYc cannot be positive.")
        self._eYc = value

    def _get_eZt(self) -> float:
        return self._eZt
    def _set_eZt(self, value: float):
        if value < 0.:
            raise ValueError("Tensile limit eZt cannot be negative.")
        self._eZt = value

    def _get_eZc(self) -> float:
        return self._eZc
    def _set_eZc(self, value: float):
        if value > 0.:
            raise ValueError("Compressive limit eZc cannot be positive.")
        self._eZc = value

    def _get_eSxy(self) -> float:
        return self._eSxy
    def _set_eSxy(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit eSxy cannot be negative.")
        self._eSxy = value

    def _get_eSxz(self) -> float:
        return self._eSxz
    def _set_eSxz(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit eSxz cannot be negative.")
        self._eSxz = value

    def _get_eSyz(self) -> float:
        return self._eSyz
    def _set_eSyz(self, value: float):
        if value < 0.:
            raise ValueError("Strain limit eSyz cannot be negative.")
        self._eSyz = value

    e1 = property(_get_e1, _set_e1,
                         doc="Activates the failure evaluation regarding the strain in the material 1 direction.")
    e2 = property(_get_e2, _set_e2,
                         doc="Activates the failure evaluation regarding the strain in the material 2 direction.")
    e3 = property(_get_e3, _set_e3,
                         doc="Activates the failure evaluation regarding the strain in the material 3 direction (out-of-plane).")
    e12 = property(_get_e12, _set_e12,
                         doc="Activates the failure evaluation regarding the in-plane shear strain e12.")
    e13 = property(_get_e13, _set_e13,
                          doc="Activates the failure evaluation regarding the interlaminar shear strain e13.")
    e23 = property(_get_e23, _set_e23,
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
    force_global_strain_limits = property(_get_force_global_strain_limits, _set_force_global_strain_limits,
                          doc="Whether to use one set of global strain limits instead of the "
                              "strain limits of the materials.")
    eXt = property(_get_eXt, _set_eXt,
                      doc="Global tensile strain limit in material direction 1.")
    eXc = property(_get_eXc, _set_eXc,
                   doc="Global compressive strain limit in material direction 1.")
    eYt = property(_get_eYt, _set_eYt,
                   doc="Global tensile strain limit in material direction 2.")
    eYc = property(_get_eYc, _set_eYc,
                   doc="Global compressive strain limit in material direction 2.")
    eZt = property(_get_eZt, _set_eZt,
                   doc="Global _set_eYc strain limit in material direction 3.")
    eZc = property(_get_eZc, _set_eZc,
                   doc="Global compressive strain limit in material direction 3.")
    eSxy = property(_get_eSxy, _set_eSxy,
                   doc="Global strain limit in material direction 12.")
    eSxz = property(_get_eSxz, _set_eSxz,
                   doc="Global strain limit in material direction 13.")
    eSyz = property(_get_eSyz, _set_eSyz,
                   doc="Global strain limit in material direction 23.")
