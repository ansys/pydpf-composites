"""Collection of enums."""

from enum import Enum


class Spot(Enum):
    """Implements an interface to access the spots of the results of layered elements."""

    bottom = 1
    middle = 2
    top = 3


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

    engineering_constants_e1: str = "young_modulus_x_direction"
    engineering_constants_e2: str = "young_modulus_y_direction"
    engineering_constants_e3: str = "young_modulus_z_direction"
    engineering_constants_e: str = "young_modulus"
    engineering_constants_g12: str = "shear_modulus_xy"
    engineering_constants_g23: str = "shear_modulus_yz"
    engineering_constants_g13: str = "shear_modulus_xz"
    engineering_constants_nu12: str = "poisson_ratio_xy"
    engineering_constants_nu23: str = "poisson_ratio_yz"
    engineering_constants_nu13: str = "poisson_ratio_xz"
    engineering_constants_nu: str = "poisson_ratio"
    strain_limits_effective_strain: str = "von_mises"
    tensile_yield_strength_effective_stress: str = "tensile_yield_strength"
    strain_limits_ext: str = "strain_tensile_x_direction"
    strain_limits_eyt: str = "strain_tensile_y_direction"
    strain_limits_ezt: str = "strain_tensile_z_direction"
    strain_limits_exc: str = "strain_compressive_x_direction"
    strain_limits_eyc: str = "strain_compressive_y_direction"
    strain_limits_ezc: str = "strain_compressive_z_direction"
    strain_limits_esxy: str = "strain_shear_xy"
    strain_limits_esyz: str = "strain_shear_yz"
    strain_limits_esxz: str = "strain_shear_xz"
    stress_limits_xt: str = "stress_tensile_x_direction"
    stress_limits_yt: str = "stress_tensile_y_direction"
    stress_limits_zt: str = "stress_tensile_z_direction"
    stress_limits_xc: str = "stress_compressive_x_direction"
    stress_limits_yc: str = "stress_compressive_y_direction"
    stress_limits_zc: str = "stress_compressive_z_direction"
    stress_limits_sxy: str = "stress_shear_xy"
    stress_limits_syz: str = "stress_shear_yz"
    stress_limits_sxz: str = "stress_shear_xz"
    thermal_conductivity_k: str = "thermal_conductivity_isotropic"
    thermal_conductivity_k1: str = "thermal_conductivity_x_direction"
    thermal_conductivity_k2: str = "thermal_conductivity_y_direction"
    thermal_conductivity_k3: str = "thermal_conductivity_z_direction"
    specific_heat_cp: str = "specific_heat"
    thermal_expansion_coefficients_a: str = "coefficient_thermal_expansion"
    thermal_expansion_coefficients_ax: str = "coefficient_thermal_expansion_x"
    thermal_expansion_coefficients_ay: str = "coefficient_thermal_expansion_y"
    thermal_expansion_coefficients_az: str = "coefficient_thermal_expansion_z"
    fabric_fiber_angle_phi: str = "fabric_fiber_angle"
    hill_yield_criterion_r11: str = "yield_stress_ratio_x_hill_criterion"
    hill_yield_criterion_r22: str = "yield_stress_ratio_y_hill_criterion"
    hill_yield_criterion_r33: str = "yield_stress_ratio_z_hill_criterion"
    hill_yield_criterion_r12: str = "yield_stress_ratio_xy_hill_criterion"
    hill_yield_criterion_r23: str = "yield_stress_ratio_yz_hill_criterion"
    hill_yield_criterion_r13: str = "yield_stress_ratio_xz_hill_criterion"
    tsai_wu_constant_xy: str = "coupling_coef_xy_tsai_wu"
    tsai_wu_constant_yz: str = "coupling_coef_yz_tsai_wu"
    tsai_wu_constant_xz: str = "coupling_coef_xz_tsai_wu"
    puck_constants_p_21_pos: str = "tensile_inclination_xz_puck_constants"
    puck_constants_p_21_neg: str = "compressive_inclination_xz_puck_constants"
    puck_constants_p_22_pos: str = "tensile_inclination_yz_puck_constants"
    puck_constants_p_22_neg: str = "compressive_inclination_yz_puck_constants"
    puck_constants_s: str = "degradation_parameter_s_puck_constants"
    puck_constants_m: str = "degradation_parameter_m_puck_constants"
    puck_constants_interface_weakening_factor: str = "interface_weakening_factor_puck_constants"
    larc_constants_fracture_angle_under_compression: str = (
        "fracture_angle_under_compression_larc_constants"
    )
    larc_constants_fracture_toughness_ratio: str = "fracture_toughness_ratio_larc_constants"
    larc_constants_fracture_toughness_mode_1: str = (
        "longitudinal_friction_coefficient_larc_constants"
    )
    larc_constants_fracture_toughness_mode_2: str = "transverse_friction_coefficient_larc_constants"


class LayerProperty(Enum):
    """Available layer properties."""

    thicknesses = 0
    angles = 1
    shear_angles = 2


class FailureMeasure(Enum):
    """Available Failure Measures."""

    inverse_reserve_factor: str = "inverse_reserve_factor"
    margin_of_safety: str = "safety_margin"
    reserve_factor: str = "safety_factor"
