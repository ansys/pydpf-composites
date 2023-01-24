"""Collection of constants used across PyDPF Composites."""

from enum import IntEnum

__all__ = ("Spot", "Sym3x3TensorComponent", "FailureOutput")


class Spot(IntEnum):
    """Implements an interface to access the spots of the results of layered elements."""

    bottom = 1
    middle = 2
    top = 3


def get_rst_spot_index(spot: Spot) -> int:
    """Return the spot in index in the rst file.

    The order in the rst file is always bottom, top, (mid)
    """
    return [-1, 0, 2, 1][spot]


class Sym3x3TensorComponent(IntEnum):
    """Tensor indices for symmetrical 3x3 tensors."""

    tensor11 = 0
    tensor22 = 1
    tensor33 = 2
    tensor21 = 3
    tensor31 = 5
    tensor32 = 4


class FailureOutput(IntEnum):
    """Failure output type. The enum value corresponds to the index in the fields container."""

    failure_mode = 0
    failure_value = 1
    max_layer_index = 2
