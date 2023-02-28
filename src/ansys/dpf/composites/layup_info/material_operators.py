"""Helper function to get material-related operators."""
from typing import Optional
from warnings import warn

from ansys.dpf.core import DataSources, Operator

__all__ = ("MaterialOperators", "get_material_operators")

from ansys.dpf.composites.unit_system import UnitSystemProvider


class MaterialOperators:
    """Provides the container for material-related operators.

    Parameters
    ----------
    material_support_provider:
        The material support provider takes care of mapping the materials in the RST file to
        the materials in the composite definitions.
        The material support contains all the materials from the RST file. Currently
        the output of this operator cannot be inspected in Python.
    material_provider:
        Outputs the ``MaterialsContainer``, which can be used to
        evaluate material properties. This container cannot be
        queried in Python, but it can be passed to other DPF operators
        that evaluate the properties.
    result_info_provider:
        Provides the ``ResultInfo`` object.
    """

    def __init__(
        self,
        material_provider: Operator,
        material_support_provider: Operator,
        result_info_provider: Operator,
    ):
        """Create a MaterialOperators object."""
        self._material_provider = material_provider
        self._material_support_provider = material_support_provider
        self._result_info_provider = result_info_provider

    @property
    def result_info_provider(self) -> Operator:
        """Get result_info_provider."""
        warn(
            "Getting the result_info_provider from a "
            "MaterialsOperators object is deprecated. "
            "Use get_unit_system to obtain the unit system.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._result_info_provider

    @property
    def material_support_provider(self) -> Operator:
        """Get material_support_provider."""
        return self._material_support_provider

    @property
    def material_provider(self) -> Operator:
        """Get material_provider."""
        return self._material_provider


def get_material_operators(
    rst_data_source: DataSources,
    engineering_data_source: DataSources,
    unit_system: Optional[UnitSystemProvider] = None,
) -> MaterialOperators:
    """Get material properties related to operators.

    Parameters
    ----------
    rst_data_source
        Data source that contains a RST file.
    engineering_data_source
        Data source that contains the Engineering Data file.
    unit_system:
        Unit System
    ----------

    """
    material_support_provider = Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.data_sources(rst_data_source)

    result_info_provider = Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    if unit_system is None:
        warn(
            "Calling get_material_operators without "
            "a unit_system argument is deprecated. Use get_unit_system "
            "to obtain the unit_system",
            DeprecationWarning,
            stacklevel=2,
        )
        unit_system = result_info_provider.outputs.result_info

    # Set up material provider
    # Combines the material support in the engineering data XML file and the unit system.
    # Its output can be used to evaluate material properties.
    material_provider = Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = engineering_data_source
    material_provider.inputs.unit_system_or_result_info(unit_system)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(engineering_data_source)

    return MaterialOperators(
        material_provider=material_provider,
        material_support_provider=material_support_provider,
        result_info_provider=result_info_provider,
    )
