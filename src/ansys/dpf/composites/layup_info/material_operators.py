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

"""Helper function to get material-related operators."""
from warnings import warn

from ansys.dpf.core import DataSources, Operator

from ansys.dpf.composites.constants import D3PLOT_KEY_AND_FILENAME
from ansys.dpf.composites.server_helpers import version_equal_or_later

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

        if version_equal_or_later(self._material_provider._server, "7.1"):
            self._material_container_helper_op = Operator("composite::materials_container_helper")
            self._material_container_helper_op.inputs.materials_container(
                self._material_provider.outputs
            )
        else:
            self._material_container_helper_op = None

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

    @property
    def material_container_helper_op(self) -> Operator:
        """
        Get material container helper operator.

        This operator can be used to access metadata of the materials.
        Return value is None if the server version does not support this operator.
        The minimum version is 2024 R1-pre0 (7.1).
        """
        return self._material_container_helper_op


def get_material_operators(
    rst_data_source: DataSources,
    engineering_data_source: DataSources,
    solver_input_data_source: DataSources | None = None,
    unit_system: UnitSystemProvider | None = None,
) -> MaterialOperators:
    """Get material properties related to operators.

    Parameters
    ----------
    rst_data_source
        Data source that contains a RST file. Note that multiple (distributed)
        RST files are not supported.
    engineering_data_source
        Data source that contains the Engineering Data file.
    solver_input_data_source
        Data source that contains the solver input file.
    unit_system:
        Unit System
    ----------

    """
    if rst_data_source.result_key == D3PLOT_KEY_AND_FILENAME:
        material_support_provider = Operator("composite::ls_dyna_material_support_provider")
        if solver_input_data_source is None:
            raise RuntimeError(
                "solver input file must be provided for the support of LSDyna (d3plot)"
            )
        material_support_provider.inputs.data_sources(solver_input_data_source)
    elif rst_data_source.result_key == "rst":
        material_support_provider = Operator("support_provider")
        material_support_provider.inputs.property("mat")
        material_support_provider.inputs.data_sources(rst_data_source)
    else:
        raise ValueError(f"Unsupported result key: {rst_data_source.result_key}")

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
    material_provider.inputs.unit_system_or_result_info(unit_system)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(engineering_data_source)

    # pylint: disable=protected-access
    if version_equal_or_later(rst_data_source._server, "9.0"):
        # BUG 1060154: Mechanical adds materials to the MAPDL model for flexible
        # Remote Points etc. These materials should be skipped by adding
        # materials without properties.
        material_provider.inputs.skip_missing_materials(True)

    return MaterialOperators(
        material_provider=material_provider,
        material_support_provider=material_support_provider,
        result_info_provider=result_info_provider,
    )
