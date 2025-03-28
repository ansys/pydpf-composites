# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Helpers to get material properties."""
from collections.abc import Collection
from dataclasses import dataclass
from enum import Enum
from typing import cast

from ansys.dpf.core import DataSources, MeshedRegion, Operator, types
import numpy as np

__all__ = (
    "MaterialMetadata",
    "MaterialProperty",
    "get_constant_property",
    "get_all_dpf_material_ids",
    "get_constant_property_dict",
    "get_material_metadata",
)

from ..constants import SolverType
from ..unit_system import UnitSystemProvider, get_unit_system
from ._layup_info import get_element_info_provider


class MaterialProperty(str, Enum):
    """Provides the material properties that are available."""

    Engineering_Constants_E1 = "young_modulus_x_direction"
    Engineering_Constants_E2 = "young_modulus_y_direction"
    Engineering_Constants_E3 = "young_modulus_z_direction"
    Engineering_Constants_E = "young_modulus"
    Engineering_Constants_G12 = "shear_modulus_xy"
    Engineering_Constants_G23 = "shear_modulus_yz"
    Engineering_Constants_G13 = "shear_modulus_xz"
    Engineering_Constants_nu12 = "poisson_ratio_xy"
    Engineering_Constants_nu23 = "poisson_ratio_yz"
    Engineering_Constants_nu13 = "poisson_ratio_xz"
    Engineering_Constants_nu = "poisson_ratio"
    Strain_Limits_effective_strain = "von_mises"
    Tensile_Yield_Strength_effective_stress = "tensile_yield_strength"
    Strain_Limits_eXt = "strain_tensile_x_direction"
    Strain_Limits_eYt = "strain_tensile_y_direction"
    Strain_Limits_eZt = "strain_tensile_z_direction"
    Strain_Limits_eXc = "strain_compressive_x_direction"
    Strain_Limits_eYc = "strain_compressive_y_direction"
    Strain_Limits_eZc = "strain_compressive_z_direction"
    Strain_Limits_eSxy = "strain_shear_xy"
    Strain_Limits_eSyz = "strain_shear_yz"
    Strain_Limits_eSxz = "strain_shear_xz"
    Stress_Limits_Xt = "stress_tensile_x_direction"
    Stress_Limits_Yt = "stress_tensile_y_direction"
    Stress_Limits_Zt = "stress_tensile_z_direction"
    Stress_Limits_Xc = "stress_compressive_x_direction"
    Stress_Limits_Yc = "stress_compressive_y_direction"
    Stress_Limits_Zc = "stress_compressive_z_direction"
    Stress_Limits_Sxy = "stress_shear_xy"
    Stress_Limits_Syz = "stress_shear_yz"
    Stress_Limits_Sxz = "stress_shear_xz"
    Thermal_Conductivity_K = "thermal_conductivity_isotropic"
    Thermal_Conductivity_K1 = "thermal_conductivity_x_direction"
    Thermal_Conductivity_K2 = "thermal_conductivity_y_direction"
    Thermal_Conductivity_K3 = "thermal_conductivity_z_direction"
    Specific_Heat_cp = "specific_heat"
    Thermal_Expansion_Coefficients_a = "coefficient_thermal_expansion"
    Thermal_Expansion_Coefficients_aX = "coefficient_thermal_expansion_x"
    Thermal_Expansion_Coefficients_aY = "coefficient_thermal_expansion_y"
    Thermal_Expansion_Coefficients_aZ = "coefficient_thermal_expansion_z"
    Fabric_Fiber_Angle_phi = "fabric_fiber_angle"
    Hill_Yield_Criterion_R11 = "yield_stress_ratio_x_hill_criterion"
    Hill_Yield_Criterion_R22 = "yield_stress_ratio_y_hill_criterion"
    Hill_Yield_Criterion_R33 = "yield_stress_ratio_z_hill_criterion"
    Hill_Yield_Criterion_R12 = "yield_stress_ratio_xy_hill_criterion"
    Hill_Yield_Criterion_R23 = "yield_stress_ratio_yz_hill_criterion"
    Hill_Yield_Criterion_R13 = "yield_stress_ratio_xz_hill_criterion"
    Tsai_Wu_Constant_xy = "coupling_coef_xy_tsai_wu"
    Tsai_Wu_Constant_yz = "coupling_coef_yz_tsai_wu"
    Tsai_Wu_Constant_xz = "coupling_coef_xz_tsai_wu"
    Puck_Constants_p_21_pos = "tensile_inclination_xz_puck_constants"
    Puck_Constants_p_21_neg = "compressive_inclination_xz_puck_constants"
    Puck_Constants_p_22_pos = "tensile_inclination_yz_puck_constants"
    Puck_Constants_p_22_neg = "compressive_inclination_yz_puck_constants"
    Puck_Constants_s = "degradation_parameter_s_puck_constants"
    Puck_Constants_m = "degradation_parameter_m_puck_constants"
    Puck_Constants_interface_weakening_factor = "interface_weakening_factor_puck_constants"
    Larc_Constants_fracture_angle_under_compression = (
        "fracture_angle_under_compression_larc_constants"
    )
    Larc_Constants_fracture_toughness_ratio = "fracture_toughness_ratio_larc_constants"
    Larc_Constants_fracture_toughness_mode_1 = "longitudinal_friction_coefficient_larc_constants"
    Larc_Constants_fracture_toughness_mode_2 = "transverse_friction_coefficient_larc_constants"


def get_constant_property(
    material_property: MaterialProperty,
    dpf_material_id: np.int64,
    materials_provider: Operator,
    unit_system: UnitSystemProvider,
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
    unit_system:
    """
    material_property_field = Operator("eng_data::ans_mat_property_field_provider")
    material_property_field.inputs.materials_container(materials_provider)
    material_property_field.inputs.dpf_mat_id(int(dpf_material_id))
    material_property_field.inputs.property_name(material_property.value)

    material_property_field.inputs.unit_system_or_result_info(unit_system)
    properties = material_property_field.get_output(output_type=types.fields_container)
    assert len(properties) == 1, "Properties container has to have exactly one entry."
    assert len(properties[0].data) == 1, (
        "Properties field has to have exactly one entry."
        "Probably the property is not constant. "
        "Variable properties are currently not supported."
    )
    return cast(float, properties[0].data[0])


def get_all_dpf_material_ids(
    mesh: MeshedRegion,
    data_source_or_streams_provider: DataSources | Operator,
    solver_type: SolverType = SolverType.MAPDL,
) -> Collection[np.int64]:
    """Get all DPF material IDs.

    Parameters
    ----------
    mesh:
        DPF meshed region enriched with lay-up information.
    data_source_or_streams_provider:
        DPF data source or stream provider that contains the RST file.
    solver_type:
        Type of result file (model). The default is ``SolverType.MAPDL``.
    """
    element_info_provider = get_element_info_provider(
        mesh=mesh,
        stream_provider_or_data_source=data_source_or_streams_provider,
        solver_type=solver_type,
    )
    all_material_ids: set["np.int64"] = set()
    for element_id in mesh.elements.scoping.ids:
        element_info = element_info_provider.get_element_info(element_id)
        if element_info is not None:
            all_material_ids.update(element_info.dpf_material_ids)
    return all_material_ids


def get_constant_property_dict(
    material_properties: Collection[MaterialProperty],
    materials_provider: Operator,
    data_source_or_streams_provider: DataSources | Operator,
    mesh: MeshedRegion,
) -> dict[np.int64, dict[MaterialProperty, float]]:
    """Get a dictionary with constant properties.

    Returns a dictionary with the DPF material ID as a key and
    a dictionary with the requested properties as the value. Only constant properties
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
    properties: dict[np.int64, dict[MaterialProperty, float]] = {}
    unit_system = get_unit_system(data_source_or_streams_provider)
    for dpf_material_id in get_all_dpf_material_ids(
        mesh=mesh, data_source_or_streams_provider=data_source_or_streams_provider
    ):
        properties[dpf_material_id] = {}
        for material_property in material_properties:
            constant_property = get_constant_property(
                material_property=material_property,
                dpf_material_id=dpf_material_id,
                materials_provider=materials_provider,
                unit_system=unit_system,
            )
            properties[dpf_material_id][material_property] = constant_property
    return properties


@dataclass(frozen=True)
class MaterialMetadata:
    """
    Material metadata such as name and ply type.

    Parameters
    ----------
    dpf_material_id:
        Material index in the DPF materials container.
    material_name:
        Name of the material. Is empty if the name is not available.
    ply_type:
        Ply type. One of regular, woven, honeycomb_core,
        isotropic_homogeneous_core, orthotropic_homogeneous_core,
        isotropic, adhesive, undefined. Regular stands for uni-directional.
        None if the DPF server older than 2025 R1 pre 0 (9.0).
    solver_material_id:
        Material index of the solver.
        None if DPF server older than 2024 R1 pre 0 (8.0).
    """

    dpf_material_id: int = 0
    material_name: str = ""
    ply_type: str | None = None
    solver_material_id: int | None = None

    @property
    def is_core(self) -> bool:
        """Returns true if the material is of type core."""
        return self.ply_type in (
            "honeycomb_core",
            "isotropic_homogeneous_core",
            "orthotropic_homogeneous_core",
        )


def get_material_metadata(
    material_container_helper_op: Operator | None,
) -> dict[int, MaterialMetadata]:
    """
    DPF material ID to metadata map of the materials.

    This data can be used to filter analysis plies
    or element layers by ply type, material name etc.

    Note: ply type is only available in DPF server version 9.0 (2025 R1 pre0) and later.
    """
    if material_container_helper_op is None:
        raise RuntimeError(
            "The used DPF server does not support the requested data. "
            "Use version 2024 R1-pre0 or later."
        )
    material_name_field = material_container_helper_op.outputs.material_names()
    if hasattr(material_container_helper_op.outputs, "solver_material_ids"):
        solver_id_field = material_container_helper_op.outputs.solver_material_ids()
    else:
        solver_id_field = None
    material_ids = material_name_field.scoping.ids
    if hasattr(material_container_helper_op.outputs, "ply_types"):
        ply_type_field = material_container_helper_op.outputs.ply_types()
    else:
        ply_type_field = None

    metadata = {}
    for dpf_mat_id in material_ids:
        metadata[dpf_mat_id] = MaterialMetadata(
            dpf_material_id=dpf_mat_id,
            material_name=material_name_field.data[material_name_field.scoping.index(dpf_mat_id)],
            ply_type=(
                ply_type_field.data[ply_type_field.scoping.index(dpf_mat_id)]
                if ply_type_field
                else None
            ),
            solver_material_id=(
                solver_id_field.data[solver_id_field.scoping.index(dpf_mat_id)]
                if solver_id_field
                else None
            ),
        )

    return metadata
