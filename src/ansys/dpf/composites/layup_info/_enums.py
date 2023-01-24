from enum import IntEnum


class LayupProperty(IntEnum):
    """Enum for Layup Properties.

    Values correspond to labels in output container of layup provider.
    """

    angle = 0
    shear_angle = 1
    thickness = 2
    laminate_offset = 3


class LayerProperty(IntEnum):
    """Available layer properties."""

    thicknesses = 0
    angles = 1
    shear_angles = 2
