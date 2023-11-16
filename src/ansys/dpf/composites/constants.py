"""Collection of constants used across PyDPF Composites."""
from enum import IntEnum

__all__ = (
    "Spot",
    "Sym3x3TensorComponent",
    "FailureOutput",
    "REF_SURFACE_NAME",
    "FAILURE_LABEL",
    "TIME_LABEL",
)

FAILURE_LABEL = "failure_label"
TIME_LABEL = "time"


class Spot(IntEnum):
    """Implements an interface to access the spots of the results of layered elements."""

    BOTTOM = 1
    MIDDLE = 2
    TOP = 3


class Sym3x3TensorComponent(IntEnum):
    """Provides tensor indices for symmetrical 3x3 tensors."""

    TENSOR11 = 0
    TENSOR22 = 1
    TENSOR33 = 2
    TENSOR21 = 3
    TENSOR31 = 5
    TENSOR32 = 4


class FailureOutput(IntEnum):
    """Provides failure output types.

    The enum value corresponds to the index in the fields container.
    """

    FAILURE_MODE = 0
    FAILURE_VALUE = 1
    MAX_LAYER_INDEX = 2
    FAILURE_MODE_REF_SURFACE = 3
    FAILURE_VALUE_REF_SURFACE = 4
    MAX_GLOBAL_LAYER_IN_STACK = 5
    MAX_LOCAL_LAYER_IN_ELEMENT = 6
    MAX_SOLID_ELEMENT_ID = 7


REF_SURFACE_NAME = "Reference Surface"
