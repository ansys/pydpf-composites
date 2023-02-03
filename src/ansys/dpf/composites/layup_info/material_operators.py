"""Helper function to get material-related operators."""

from dataclasses import dataclass

from ansys.dpf.core import DataSources, Operator

__all__ = ("MaterialOperators", "get_material_operators")


@dataclass(frozen=True)
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

    material_provider: Operator
    material_support_provider: Operator
    result_info_provider: Operator


def get_material_operators(
    rst_data_source: DataSources, engineering_data_source: DataSources
) -> MaterialOperators:
    """Get material properties related to operators.

    Parameters
    ----------
    rst_data_source
        Data source that contains a RST file.
    engineering_data_source
        Data source that contains the Engineering Data file.
    ----------

    """
    material_support_provider = Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.data_sources(rst_data_source)

    # Get result info
    # This is needed provides the unit system from the rst file
    result_info_provider = Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    # Set up material provider
    # Combines the material support in the engineering data XML file and the unit system.
    # Its output can be used to evaluate material properties.
    material_provider = Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = engineering_data_source
    material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(engineering_data_source)

    return MaterialOperators(
        material_provider=material_provider,
        result_info_provider=result_info_provider,
        material_support_provider=material_support_provider,
    )
