"""Module for the post-processing of composite structures."""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .enums import Spot
from .layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfo,
    ElementInfoProvider,
    get_analysis_ply,
    get_element_info_provider,
)
from .result_definition import ResultDefinition
from .sampling_point import SamplingPoint
from .select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_material_id,
)

__all__ = [
    "ResultDefinition",
    "SamplingPoint",
    "Spot",
    "ResultDefinition",
    "ElementInfoProvider",
    "ElementInfo",
    "get_analysis_ply",
    "AnalysisPlyInfoProvider",
    "get_element_info_provider",
    "get_selected_indices",
    "get_selected_indices_by_material_id",
    "get_selected_indices_by_analysis_ply",
]
