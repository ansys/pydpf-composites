"""Module for the post-processing of composite structures."""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .add_layup_info_to_mesh import add_layup_info_to_mesh
from .composite_data_sources import CompositeDataSources, ContinuousFiberCompositesFiles
from .composite_model import CompositeModel
from .enums import MaterialProperty, Spot
from .layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfo,
    ElementInfoProvider,
    LayupPropertiesProvider,
    get_dpf_material_id_by_analyis_ply_map,
    get_element_info_provider,
)
from .material_properties import (
    get_all_dpf_material_ids,
    get_constant_property,
    get_constant_property_dict,
)
from .material_setup import MaterialOperators
from .result_definition import ResultDefinition
from .sampling_point import SamplingPoint
from .select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)

__all__ = [
    "CompositeModel",
    "CompositeDataSources",
    "add_layup_info_to_mesh",
    "MaterialOperators",
    "ResultDefinition",
    "SamplingPoint",
    "Spot",
    "ResultDefinition",
    "ElementInfoProvider",
    "ElementInfo",
    "get_dpf_material_id_by_analyis_ply_map",
    "AnalysisPlyInfoProvider",
    "get_element_info_provider",
    "get_selected_indices",
    "get_selected_indices_by_dpf_material_ids",
    "get_selected_indices_by_analysis_ply",
    "LayupPropertiesProvider",
    "get_constant_property",
    "get_all_dpf_material_ids",
    "get_constant_property_dict",
    "MaterialProperty",
    "ContinuousFiberCompositesFiles",
]
