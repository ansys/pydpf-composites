"""Unit system helper."""
__all__ = ("get_unit_system", "UnitSystemProvider")

from typing import Optional, Union

from ansys.dpf.core import DataSources, Operator, UnitSystem

# Either a UnitSystem or a ResultInfoProvider operator.
# This Union is needed because dpf currently does not support passing
# a ResultInfo directly to operators nor is it possible to get
# the UnitSystem from a ResultInfo.
UnitSystemProvider = Union[UnitSystem, Operator]


def get_unit_system(
    rst_data_source: DataSources, default_unit_system: Optional[UnitSystem] = None
) -> UnitSystemProvider:
    """Get unit_system from rst DataSources.

    Returns the ResultInfo from the result file or
    the default_unit_system if no unit system is found in the result file
    (for example for pure mapdl result files).

    Parameters
    ----------
    rst_data_source:
        DPF Data Source containing a rst file.
    default_unit_system:
        Default Unit system that is used if the rst file does not contain
        a unit system.
    """
    result_info_provider = Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)

    # If unit system is undefined, fall back to default_unit_system
    if result_info_provider.outputs.result_info().unit_system == "Undefined":
        if default_unit_system is None:
            raise RuntimeError(
                "The result file does not specify a unit system."
                " Please define a default unit system. "
                "A default unit system can be passed when "
                "creating a CompositeModel."
            )
        return default_unit_system
    else:
        return result_info_provider