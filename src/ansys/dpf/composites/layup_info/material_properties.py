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


class MaterialProperty(str, Enum):
    """Provides the material properties that are available."""

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


def get_constant_property(
    material_property: MaterialProperty,
    dpf_material_id: np.int64,
    materials_provider: Operator,
    data_source_or_streams_provider: Union[DataSources, Operator],
) -> float:
    """Get a constant material property.

    Only constant properties are supported. Variable properties are evaluated at their
    default values.

    Parameters
    ----------
    material_property:
        Material property.
    dpf_material_id:
        DPF material ID.
    materials_provider:
        DPF Materials provider operator. This value is available from the
        :attr:`.CompositeModel.material_operators` attribute.
    data_source_or_streams_provider:
        Data source or streams provider that contains the RST file.
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
    assert len(properties) == 1, "Properties container has to have exactly one entry."
    assert len(properties[0].data) == 1, (
        "Properties field has to have exactly one entry."
        "Probably the property is not constant. "
        "Variable properties are currently not supported."
    )
    return cast(float, properties[0].data[0])


def get_all_dpf_material_ids(
    mesh: MeshedRegion, data_source_or_streams_provider: Union[DataSources, Operator]
) -> Collection[np.int64]:
    """Get all DPF material IDs.

    Parameters
    ----------
    mesh:
        DPF meshed region enriched with lay-up information.
    data_source_or_streams_provider:
        DPF data source or stream provider that contains the RST file.
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

    Returns a dictionary with the DPF material ID as a key and
    a dictionaory with the requested properties as the value. Only constant properties
    are supported. Variable properties are evaluated at their
    default values.
    Because this method can be slow to evaluate, it should not
    be called in a loop.

    Parameters
    ----------
    material_properties:
        Material properties to request.
    materials_provider:
        DPF Materials provider operator. This value is Available from the
        :attr:`.CompositeModel.material_operators` attribute.
    data_source_or_streams_provider:
        DPF data source or stream provider that contains the RST file.
    mesh:
        DPF meshed region enriched with lay-up information.
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
