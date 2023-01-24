"""Helpers to get material properties."""
from enum import Enum
from typing import Collection, Dict, Union, cast

from ansys.dpf.core import DataSources, MeshedRegion, Operator, types
import numpy as np

from ._layup_info import get_dpf_material_id_by_analyis_ply_map

__all__ = (
    "MaterialProperty",
    "get_constant_property",
    "get_all_dpf_material_ids",
    "get_constant_property_dict",
)


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


def get_constant_property(
    material_property: MaterialProperty,
    dpf_material_id: np.int64,
    materials_provider: Operator,
    data_source_or_streams_provider: Union[DataSources, Operator],
) -> float:
    """Get a constant material property.

    Only constant properties
    are supported. Variable properties are evaluated at their
    default value.

    Parameters
    ----------
    material_property:
        material property
    dpf_material_id:
    materials_provider:
        Dpf Materials provider operator. Available from CompositeModel:
        :class:`CompositeModel.material_operators`
    data_source_or_streams_provider:
        Data source or streams provider that contains a rst file
    """
    material_property_field = Operator("eng_data::ans_mat_property_field_provider")
    material_property_field.inputs.materials_container(materials_provider)
    material_property_field.inputs.dpf_mat_id(int(dpf_material_id))
    material_property_field.inputs.property_name(material_property.value)
    result_info_provider = Operator("ResultInfoProvider")
    if isinstance(data_source_or_streams_provider, DataSources):
        result_info_provider.inputs.data_sources(data_source_or_streams_provider)
    else:
        result_info_provider.inputs.streams_container(data_source_or_streams_provider)
    material_property_field.inputs.unit_system_or_result_info(result_info_provider)
    properties = material_property_field.get_output(output_type=types.fields_container)
    assert len(properties) == 1, "Properties Container has to have exactly one entry"
    assert len(properties[0].data) == 1, (
        "Properties Field as to have exactly one entry. "
        "Probably the property is not constant. "
        "Variable properties are currently not supported."
    )
    return cast(float, properties[0].data[0])


def get_all_dpf_material_ids(
    mesh: MeshedRegion, data_source_or_streams_provider: Union[DataSources, Operator]
) -> Collection[np.int64]:
    """Get all the dpf_material_ids.

    Parameters
    ----------
    mesh:
        Dpf MeshedRegion enriched with layup information
    data_source_or_streams_provider:
        Dpf DataSource or StreamProvider that contains a rst file
    """
    id_to_material_map = get_dpf_material_id_by_analyis_ply_map(
        mesh, data_source_or_streams_provider
    )
    return set(id_to_material_map.values())


def get_constant_property_dict(
    material_properties: Collection[MaterialProperty],
    materials_provider: Operator,
    data_source_or_streams_provider: Union[DataSources, Operator],
    mesh: MeshedRegion,
) -> Dict[np.int64, Dict[MaterialProperty, float]]:
    """Get a dictionary with constant properties.

    Returns a dictionary with the dpf_material_id as key and
    a dict with the requested properties as the value. Only constant properties
    are supported. Variable properties are evaluated at their
    default value.
    This function can be slow to evaluate and should not
    be called in a loop.

    Parameters
    ----------
    material_properties:
        Requested material properties
    materials_provider:
    data_source_or_streams_provider:
        Dpf DataSource or StreamProvider that contains a rst file
    mesh:
        Dpf MeshedRegion enriched with layup information
    """
    properties: Dict[np.int64, Dict[MaterialProperty, float]] = {}
    for dpf_material_id in get_all_dpf_material_ids(
        mesh=mesh, data_source_or_streams_provider=data_source_or_streams_provider
    ):
        properties[dpf_material_id] = {}
        for material_property in material_properties:
            constant_property = get_constant_property(
                material_property=material_property,
                dpf_material_id=dpf_material_id,
                materials_provider=materials_provider,
                data_source_or_streams_provider=data_source_or_streams_provider,
            )
            properties[dpf_material_id][material_property] = constant_property
    return properties
