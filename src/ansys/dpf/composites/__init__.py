"""Module for the post-processing of composite structures."""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .result_definition import ResultDefinition
from .sampling_point import SamplingPoint

__all__ = [
    "ResultDefinition",
    "SamplingPoint"
]