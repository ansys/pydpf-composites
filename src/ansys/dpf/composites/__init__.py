
try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

"""
from .failure_criteria import (
    MaxStrainCriterion, 
    MaxStressCriterion,
    CoreFailureCriterion,
    CuntzeCriterion,
    FaceSheetWrinklingCriterion,
    HashinCriterion,
    HoffmanCriterion,
    LaRCCriterion,
    PuckCriterion,
    ShearCrimpingCriterion,
    TsaiHillCriterion,
    TsaiWuCriterion,
    VonMisesCriterion,
    CombinedFailureCriterion
    )
"""
from .result_definition import ResultDefinition