
try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .failure_criteria import (
    MaxStrainCriterion, 
    MaxStressCriterion,
    CombinedFailureCriterion
    )

from .result_definition import ResultDefinition