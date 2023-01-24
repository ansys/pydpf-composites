from enum import IntEnum


class LayupProperty(IntEnum):
    """Enum for Layup Properties.

    Values correspond to labels in output container of layup provider.
    """

    ANGLE = 0
    SHEAR_ANGLE = 1
    THICKNESS = 2
    LAMINATE_OFFSET = 3


class LayerProperty(IntEnum):
    """Available layer properties."""

    THICKNESSES = 0
    ANGLES = 1
    SHEAR_ANGLES = 2
