"""Collection of enums."""

from enum import Enum


class Spot(Enum):
    """Implements an interface to access the spots of the results of layered elements."""

    BOTTOM = 1
    MIDDLE = 2
    TOP = 3
