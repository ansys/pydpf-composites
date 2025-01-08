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

from dataclasses import dataclass

from ansys.dpf.core import DataSources, Field, Operator, PropertyField

from ansys.dpf.composites.unit_system import UnitSystemProvider


@dataclass(frozen=True)
class _ReferenceSurfaceMeshAndMappingField:
    mesh: Field
    mapping_field: Field


def _get_reference_surface_and_mapping_field(
    data_sources: DataSources, unit_system: UnitSystemProvider
) -> _ReferenceSurfaceMeshAndMappingField:
    ref_surface_operator = Operator("composite::reference_surface_operator")
    ref_surface_operator.inputs.data_sources.connect(data_sources)
    ref_surface_operator.inputs.unit_system.connect(unit_system)
    return _ReferenceSurfaceMeshAndMappingField(
        mesh=ref_surface_operator.outputs.mesh(),
        mapping_field=ref_surface_operator.outputs.mapping_field(),
    )


def _get_map_to_reference_surface_operator(
    reference_surface_and_mapping_field: _ReferenceSurfaceMeshAndMappingField,
    element_layer_indices_field: PropertyField,
) -> Operator:
    map_to_reference_surface_operator = Operator("composite::map_to_reference_surface_operator")
    map_to_reference_surface_operator.inputs.mapping_field.connect(
        reference_surface_and_mapping_field.mapping_field
    )
    map_to_reference_surface_operator.inputs.mesh.connect(reference_surface_and_mapping_field.mesh)
    map_to_reference_surface_operator.inputs.layers_per_element.connect(element_layer_indices_field)
    return map_to_reference_surface_operator
