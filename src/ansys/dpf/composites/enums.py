"""Collection of enums."""

from enum import Enum


class Spot(Enum):
    """Implements an interface to access the spots of the results of layered elements."""

    BOTTOM = 1
    MIDDLE = 2
    TOP = 3


def get_rst_spot_index(spot: Spot) -> int:
    """Return to spot in index in the rst file.

    The order in the rst file is always bottom, top, (mid)
    """
    return [-1, 0, 2, 1][spot.value]


class Sym3x3TensorComponent(Enum):
    """Tensor indices for symmetrical 3x3 tensors."""

    tensor11 = 0
    tensor22 = 1
    tensor33 = 2
    tensor21 = 3
    tensor31 = 5
    tensor32 = 4
