"""Collection of constants used across PyDPF Composites."""

from enum import IntEnum

__all__ = ("Spot", "Sym3x3TensorComponent", "FailureOutput")


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
