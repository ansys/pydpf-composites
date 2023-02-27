"""Unit system helper."""
__all__ = ("get_unit_system",)

from typing import Optional, Union

from ansys.dpf.core import DataSources, Operator, ResultInfo, UnitSystem


def get_unit_system(
    rst_data_source: DataSources, default_unit_system: Optional[UnitSystem] = None
) -> Union[UnitSystem, ResultInfo]:
    """Get unit_system from rst DataSources.

    Returns the ResultInfo from the result file or
    the default_unit_system if no unit system is found in the result file
    (for example for pure mapdl result files).

    Parameters
    ----------
    rst_data_source:
    default_unit_system:
    """
    result_info_provider = Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    rst_result_info = result_info_provider.outputs.result_info()

    # If unit system is undefined, fall back to default_unit_system
    if rst_result_info.unit_system == "Undefined":
        if default_unit_system is None:
            raise RuntimeError(
                "The result file does not specify a unit system."
                " Please define a default unit system. "
                "A default unit system can be passed when "
                "creating a CompositeModel."
            )
        return default_unit_system
    else:
        return rst_result_info
