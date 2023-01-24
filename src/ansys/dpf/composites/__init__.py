"""Module for the post-processing of composite structures."""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from . import (
    composite_model,
    constants,
    data_sources,
    failure_criteria,
    layup_info,
    result_definition,
    sampling_point,
    select_indices,
    server_helpers,
)

__all__ = (
    "composite_model",
    "constants",
    "data_sources",
    "failure_criteria",
    "layup_info",
    "result_definition",
    "sampling_point",
    "server_helpers",
    "select_indices",
)
