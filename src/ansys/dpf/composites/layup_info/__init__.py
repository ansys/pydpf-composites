"""Provides methods for reading the composite lay-up information."""

from . import material_operators, material_properties
from ._add_layup_info_to_mesh import add_layup_info_to_mesh
from ._enums import LayerProperty, LayupProperty
from ._layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfo,
    ElementInfoProvider,
    LayupPropertiesProvider,
    get_all_analysis_ply_names,
    get_analysis_ply_index_to_name_map,
    get_dpf_material_id_by_analyis_ply_map,
    get_element_info_provider,
)

__all__ = (
    "add_layup_info_to_mesh",
    "AnalysisPlyInfoProvider",
    "ElementInfo",
    "ElementInfoProvider",
    "LayerProperty",
    "LayupProperty",
    "LayupPropertiesProvider",
    "get_all_analysis_ply_names",
    "get_analysis_ply_index_to_name_map",
    "get_dpf_material_id_by_analyis_ply_map",
    "get_element_info_provider",
    "material_properties",
    "material_operators",
)
