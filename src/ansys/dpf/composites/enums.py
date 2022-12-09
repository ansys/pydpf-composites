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


class MaterialProperty(Enum):
    """Available material properties."""

    young_modulus_x_direction = "young_modulus_x_direction"
    young_modulus_y_direction = "young_modulus_y_direction"
    young_modulus_z_direction = "young_modulus_z_direction"
    young_modulus = "young_modulus"
    shear_modulus_xy = "shear_modulus_xy"
    shear_modulus_yz = "shear_modulus_yz"
    shear_modulus_xz = "shear_modulus_xz"
    poisson_ratio_xy = "poisson_ratio_xy"
    poisson_ratio_yz = "poisson_ratio_yz"
    poisson_ratio_xz = "poisson_ratio_xz"
    poisson_ratio = "poisson_ratio"
    von_mises = "von_mises"
    tensile_yield_strength = "tensile_yield_strength"
    strain_tensile_x_direction = "strain_tensile_x_direction"
    strain_tensile_y_direction = "strain_tensile_y_direction"
    strain_tensile_z_direction = "strain_tensile_z_direction"
    strain_compressive_x_direction = "strain_compressive_x_direction"
    strain_compressive_y_direction = "strain_compressive_y_direction"
    strain_compressive_z_direction = "strain_compressive_z_direction"
    strain_shear_xy = "strain_shear_xy"
    strain_shear_yz = "strain_shear_yz"
    strain_shear_xz = "strain_shear_xz"
    stress_tensile_x_direction = "stress_tensile_x_direction"
    stress_tensile_y_direction = "stress_tensile_y_direction"
    stress_tensile_z_direction = "stress_tensile_z_direction"
    stress_compressive_x_direction = "stress_compressive_x_direction"
    stress_compressive_y_direction = "stress_compressive_y_direction"
    stress_compressive_z_direction = "stress_compressive_z_direction"
    stress_shear_xy = "stress_shear_xy"
    stress_shear_yz = "stress_shear_yz"
    stress_shear_xz = "stress_shear_xz"
    thermal_conductivity_isotropic = "thermal_conductivity_isotropic"
    thermal_conductivity_x_direction = "thermal_conductivity_x_direction"
    thermal_conductivity_y_direction = "thermal_conductivity_y_direction"
    thermal_conductivity_z_direction = "thermal_conductivity_z_direction"
    specific_heat = "specific_heat"
    coefficient_thermal_expansion = "coefficient_thermal_expansion"
    coefficient_thermal_expansion_x = "coefficient_thermal_expansion_x"
    coefficient_thermal_expansion_y = "coefficient_thermal_expansion_y"
    coefficient_thermal_expansion_z = "coefficient_thermal_expansion_z"
    fabric_fiber_angle = "fabric_fiber_angle"
    yield_stress_ratio_x_hill_criterion = "yield_stress_ratio_x_hill_criterion"
    yield_stress_ratio_y_hill_criterion = "yield_stress_ratio_y_hill_criterion"
    yield_stress_ratio_z_hill_criterion = "yield_stress_ratio_z_hill_criterion"
    yield_stress_ratio_xy_hill_criterion = "yield_stress_ratio_xy_hill_criterion"
    yield_stress_ratio_yz_hill_criterion = "yield_stress_ratio_yz_hill_criterion"
    yield_stress_ratio_xz_hill_criterion = "yield_stress_ratio_xz_hill_criterion"
    coupling_coef_xy_tsai_wu = "coupling_coef_xy_tsai_wu"
    coupling_coef_yz_tsai_wu = "coupling_coef_yz_tsai_wu"
    coupling_coef_xz_tsai_wu = "coupling_coef_xz_tsai_wu"
    tensile_inclination_xz_puck_constants = "tensile_inclination_xz_puck_constants"
    compressive_inclination_xz_puck_constants = "compressive_inclination_xz_puck_constants"
    tensile_inclination_yz_puck_constants = "tensile_inclination_yz_puck_constants"
    compressive_inclination_yz_puck_constants = "compressive_inclination_yz_puck_constants"
    degradation_parameter_s_puck_constants = "degradation_parameter_s_puck_constants"
    degradation_parameter_m_puck_constants = "degradation_parameter_m_puck_constants"
    interface_weakening_factor_puck_constants = "interface_weakening_factor_puck_constants"
    fracture_angle_under_compression_larc_constants = (
        "fracture_angle_under_compression_larc_constants"
    )
    fracture_toughness_ratio_larc_constants = "fracture_toughness_ratio_larc_constants"
    longitudinal_friction_coefficient_larc_constants = (
        "longitudinal_friction_coefficient_larc_constants"
    )
    transverse_friction_coefficient_larc_constants = (
        "transverse_friction_coefficient_larc_constants"
    )
