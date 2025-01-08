# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Unit system helper."""
__all__ = ("get_unit_system", "UnitSystemProvider")

from typing import Union

from ansys.dpf.core import DataSources, Operator, UnitSystem

# Either a UnitSystem or a ResultInfoProvider operator.
# This Union is needed because dpf currently does not support passing
# a ResultInfo directly to operators nor is it possible to get
# the UnitSystem from a ResultInfo.
UnitSystemProvider = Union[UnitSystem, Operator]


def get_unit_system(
    data_source_or_streams_provider: DataSources | Operator,
    default_unit_system: UnitSystem | None = None,
) -> UnitSystemProvider:
    """Get unit_system from rst DataSources.

    Returns the ResultInfo from the result file or
    the default_unit_system if no unit system is found in the result file
    (for example for pure mapdl result files).

    Parameters
    ----------
    data_source_or_streams_provider:
        DPF Data Source or streams provider containing a rst file.
    default_unit_system:
        Default Unit system that is used if the rst file does not contain
        a unit system.
    """
    result_info_provider = Operator("ResultInfoProvider")
    if isinstance(data_source_or_streams_provider, Operator):
        result_info_provider.inputs.streams_container(data_source_or_streams_provider)
    else:
        result_info_provider.inputs.data_sources(data_source_or_streams_provider)

    # If unit system is undefined, fall back to default_unit_system
    if result_info_provider.outputs.result_info().unit_system == "Undefined":
        if default_unit_system is None:
            raise RuntimeError(
                "The result file does not specify a unit system."
                " A default unit system must be defined.. "
                "It can be passed when creating a CompositeModel."
            )
        return default_unit_system
    else:
        return result_info_provider
