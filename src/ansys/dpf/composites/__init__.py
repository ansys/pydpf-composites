"""Module for the post-processing of composite structures."""
from .material import MaterialId

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .enums import MaterialProperty, Spot
from .layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfo,
    ElementInfoProvider,
    LayupPropertiesProvider,
    get_element_info_provider,
)
from .material_properties import (
    get_all_material_ids,
    get_constant_property,
    get_constant_property_dict,
)
from .result_definition import ResultDefinition
from .sampling_point import SamplingPoint
from .select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_material_ids,
)

__all__ = [
    "ResultDefinition",
    "SamplingPoint",
    "Spot",
    "ResultDefinition",
    "ElementInfoProvider",
    "ElementInfo",
    "AnalysisPlyInfoProvider",
    "get_element_info_provider",
    "get_selected_indices",
    "get_selected_indices_by_material_ids",
    "get_selected_indices_by_analysis_ply",
    "LayupPropertiesProvider",
    "get_constant_property",
    "get_all_material_ids",
    "get_constant_property_dict",
    "MaterialProperty",
    "MaterialId",
]
