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

"""Provides methods for reading the composite lay-up information."""

from . import material_operators, material_properties
from ._add_layup_info_to_mesh import add_layup_info_to_mesh
from ._element_info import (
    ElementInfo,
    ElementInfoProvider,
    ElementInfoProviderLSDyna,
    ElementInfoProviderProtocol,
)
from ._enums import LayerProperty, LayupProperty
from ._layup_info import (
    AnalysisPlyInfo,
    AnalysisPlyInfoProvider,
    LayupModelContextType,
    LayupPropertiesProvider,
    get_all_analysis_ply_names,
    get_analysis_ply_index_to_name_map,
    get_dpf_material_id_by_analyis_ply_map,
    get_dpf_material_id_by_analysis_ply_map,
    get_element_info_provider,
    get_material_names_to_dpf_material_index,
)
from ._solid_stack_info import SolidStack, SolidStackProvider

__all__ = (
    "add_layup_info_to_mesh",
    "AnalysisPlyInfo",
    "AnalysisPlyInfoProvider",
    "ElementInfo",
    "ElementInfoProvider",
    "ElementInfoProviderLSDyna",
    "ElementInfoProviderProtocol",
    "LayerProperty",
    "LayupProperty",
    "LayupPropertiesProvider",
    "LayupModelContextType",
    "SolidStack",
    "SolidStackProvider",
    "get_all_analysis_ply_names",
    "get_analysis_ply_index_to_name_map",
    "get_dpf_material_id_by_analyis_ply_map",
    "get_dpf_material_id_by_analysis_ply_map",
    "get_element_info_provider",
    "get_material_names_to_dpf_material_index",
    "material_properties",
    "material_operators",
)
