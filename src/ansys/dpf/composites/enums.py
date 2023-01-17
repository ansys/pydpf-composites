"""Collection of enums."""

from enum import Enum


class Spot(Enum):
    """Implements an interface to access the spots of the results of layered elements."""

    BOTTOM = 1
    MIDDLE = 2
    TOP = 3


def get_rst_spot_index(spot: Spot) -> int:
    """Return the spot in index in the rst file.

    The order in the rst file is always bottom, top, (mid)
    """
    return [-1, 0, 2, 1][spot.value]


class Sym3x3TensorComponent(Enum):
    """Tensor indices for symmetrical 3x3 tensors."""

    tensor11 = 0
    tensor22 = 1
    tensor33 = 2
    tensor21 = 3
    tensor31 = 5
    tensor32 = 4


class FailureOutput(Enum):
    """Failure output type. The enum value corresponds to the index in the fields container."""

    failure_mode = 0
    failure_value = 1
    max_layer_index = 2


class LayupProperty(Enum):
    """Enum for Layup Properties.

    Values correspond to labels in output container of layup provider.
    """

    angle = 0
    shear_angle = 1
    thickness = 2
    laminate_offset = 3


class MaterialProperty(Enum):
    """Available material properties."""

    Engineering_Constants_E1: str = "young_modulus_x_direction"
    Engineering_Constants_E2: str = "young_modulus_y_direction"
    Engineering_Constants_E3: str = "young_modulus_z_direction"
    Engineering_Constants_E: str = "young_modulus"
    Engineering_Constants_G12: str = "shear_modulus_xy"
    Engineering_Constants_G23: str = "shear_modulus_yz"
    Engineering_Constants_G13: str = "shear_modulus_xz"
    Engineering_Constants_nu12: str = "poisson_ratio_xy"
    Engineering_Constants_nu23: str = "poisson_ratio_yz"
    Engineering_Constants_nu13: str = "poisson_ratio_xz"
    Engineering_Constants_nu: str = "poisson_ratio"
    Strain_Limits_effective_strain: str = "von_mises"
    Tensile_Yield_Strength_effective_stress: str = "tensile_yield_strength"
    Strain_Limits_eXt: str = "strain_tensile_x_direction"
    Strain_Limits_eYt: str = "strain_tensile_y_direction"
    Strain_Limits_eZt: str = "strain_tensile_z_direction"
    Strain_Limits_eXc: str = "strain_compressive_x_direction"
    Strain_Limits_eYc: str = "strain_compressive_y_direction"
    Strain_Limits_eZc: str = "strain_compressive_z_direction"
    Strain_Limits_eSxy: str = "strain_shear_xy"
    Strain_Limits_eSyz: str = "strain_shear_yz"
    Strain_Limits_eSxz: str = "strain_shear_xz"
    Stress_Limits_Xt: str = "stress_tensile_x_direction"
    Stress_Limits_Yt: str = "stress_tensile_y_direction"
    Stress_Limits_Zt: str = "stress_tensile_z_direction"
    Stress_Limits_Xc: str = "stress_compressive_x_direction"
    Stress_Limits_Yc: str = "stress_compressive_y_direction"
    Stress_Limits_Zc: str = "stress_compressive_z_direction"
    Stress_Limits_Sxy: str = "stress_shear_xy"
    Stress_Limits_Syz: str = "stress_shear_yz"
    Stress_Limits_Sxz: str = "stress_shear_xz"
    Thermal_Conductivity_K: str = "thermal_conductivity_isotropic"
    Thermal_Conductivity_K1: str = "thermal_conductivity_x_direction"
    Thermal_Conductivity_K2: str = "thermal_conductivity_y_direction"
    Thermal_Conductivity_K3: str = "thermal_conductivity_z_direction"
    Specific_Heat_cp: str = "specific_heat"
    Thermal_Expansion_Coefficients_a: str = "coefficient_thermal_expansion"
    Thermal_Expansion_Coefficients_aX: str = "coefficient_thermal_expansion_x"
    Thermal_Expansion_Coefficients_aY: str = "coefficient_thermal_expansion_y"
    Thermal_Expansion_Coefficients_aZ: str = "coefficient_thermal_expansion_z"
    Fabric_Fiber_Angle_phi: str = "fabric_fiber_angle"
    Hill_Yield_Criterion_R11: str = "yield_stress_ratio_x_hill_criterion"
    Hill_Yield_Criterion_R22: str = "yield_stress_ratio_y_hill_criterion"
    Hill_Yield_Criterion_R33: str = "yield_stress_ratio_z_hill_criterion"
    Hill_Yield_Criterion_R12: str = "yield_stress_ratio_xy_hill_criterion"
    Hill_Yield_Criterion_R23: str = "yield_stress_ratio_yz_hill_criterion"
    Hill_Yield_Criterion_R13: str = "yield_stress_ratio_xz_hill_criterion"
    Tsai_Wu_Constant_xy: str = "coupling_coef_xy_tsai_wu"
    Tsai_Wu_Constant_yz: str = "coupling_coef_yz_tsai_wu"
    Tsai_Wu_Constant_xz: str = "coupling_coef_xz_tsai_wu"
    Puck_Constants_p_21_pos: str = "tensile_inclination_xz_puck_constants"
    Puck_Constants_p_21_neg: str = "compressive_inclination_xz_puck_constants"
    Puck_Constants_p_22_pos: str = "tensile_inclination_yz_puck_constants"
    Puck_Constants_p_22_neg: str = "compressive_inclination_yz_puck_constants"
    Puck_Constants_s: str = "degradation_parameter_s_puck_constants"
    Puck_Constants_m: str = "degradation_parameter_m_puck_constants"
    Puck_Constants_interface_weakening_factor: str = "interface_weakening_factor_puck_constants"
    Larc_Constants_fracture_angle_under_compression: str = (
        "fracture_angle_under_compression_larc_constants"
    )
    Larc_Constants_fracture_toughness_ratio: str = "fracture_toughness_ratio_larc_constants"
    Larc_Constants_fracture_toughness_mode_1: str = (
        "longitudinal_friction_coefficient_larc_constants"
    )
    Larc_Constants_fracture_toughness_mode_2: str = "transverse_friction_coefficient_larc_constants"


class LayerProperty(Enum):
    """Available layer properties."""

    thicknesses = 0
    angles = 1
    shear_angles = 2


class FailureMeasure(Enum):
    """Available Failure Measures."""

    inverse_reserve_factor: str = "inverse_reserve_factor"
    margin_of_safety: str = "margin_of_safety"
    reserve_factor: str = "reserve_factor"
