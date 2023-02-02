from enum import IntEnum


class LayupProperty(IntEnum):
    """Enum for lay-up properties.

    Values correspond to labels in the output container of the lay-up provider.
    """

    ANGLE = 0
    SHEAR_ANGLE = 1
    THICKNESS = 2
    LAMINATE_OFFSET = 3


class LayerProperty(IntEnum):
    """Provides the layer properties available."""

    THICKNESSES = 0
    ANGLES = 1
    SHEAR_ANGLES = 2
