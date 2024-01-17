# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

from ansys.dpf.core import Operator
import pytest

from ansys.dpf.composites.data_sources import get_composites_data_sources
from ansys.dpf.composites.layup_info import LayupPropertiesProvider, add_layup_info_to_mesh
from ansys.dpf.composites.layup_info.material_operators import get_material_operators
from ansys.dpf.composites.server_helpers import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.unit_system import get_unit_system

from .helper import get_basic_shell_files


def test_layup_properties(dpf_server):
    files = get_basic_shell_files()
    files = upload_continuous_fiber_composite_files_to_server(files, dpf_server)

    composite_data_sources = get_composites_data_sources(files)
    mesh_provider = Operator("MeshProvider")
    mesh_provider.inputs.data_sources(composite_data_sources.rst)
    mesh = mesh_provider.outputs.mesh()

    unit_system = get_unit_system(composite_data_sources.rst)
    material_operators = get_material_operators(
        composite_data_sources.rst, composite_data_sources.engineering_data, unit_system=unit_system
    )
    layup_provider = add_layup_info_to_mesh(
        composite_data_sources,
        mesh=mesh,
        material_operators=material_operators,
        unit_system=unit_system,
    )

    properties_provider = LayupPropertiesProvider(layup_provider, mesh=mesh)

    angles_by_element = [
        properties_provider.get_layer_angles(element_id) for element_id in mesh.elements.scoping.ids
    ]

    six_layers = [45, 0, 0, 0, 0, 45]
    five_layers = [45, 0, 0, 0, 45]
    assert angles_by_element[0] == pytest.approx(six_layers)
    assert angles_by_element[1] == pytest.approx(six_layers)
    assert angles_by_element[2] == pytest.approx(five_layers)
    assert angles_by_element[3] == pytest.approx(five_layers)

    thickness_by_element = [
        properties_provider.get_layer_thicknesses(element_id)
        for element_id in mesh.elements.scoping.ids
    ]

    six_layers = [0.00025, 0.0002, 0.0002, 0.005, 0.0002, 0.00025]
    five_layers = [0.00025, 0.0002, 0.005, 0.0002, 0.00025]
    assert thickness_by_element[0] == pytest.approx(six_layers)
    assert thickness_by_element[1] == pytest.approx(six_layers)
    assert thickness_by_element[2] == pytest.approx(five_layers)
    assert thickness_by_element[3] == pytest.approx(five_layers)

    offset_by_element = [
        properties_provider.get_element_laminate_offset(element_id)
        for element_id in mesh.elements.scoping.ids
    ]

    assert offset_by_element[0] == pytest.approx(-0.00305)
    assert offset_by_element[1] == pytest.approx(-0.00305)
    assert offset_by_element[2] == pytest.approx(-0.00295)
    assert offset_by_element[3] == pytest.approx(-0.00295)

    shear_angle_by_element = [
        properties_provider.get_layer_shear_angles(element_id)
        for element_id in mesh.elements.scoping.ids
    ]

    six_layers = [0, 0, 0, 0, 0, 0]
    five_layers = [0, 0, 0, 0, 0]
    assert shear_angle_by_element[0] == pytest.approx(six_layers)
    assert shear_angle_by_element[1] == pytest.approx(six_layers)
    assert shear_angle_by_element[2] == pytest.approx(five_layers)
    assert shear_angle_by_element[3] == pytest.approx(five_layers)

    plies_by_element = [
        properties_provider.get_analysis_plies(element_id)
        for element_id in mesh.elements.scoping.ids
    ]

    six_layers = [
        "P1L1__woven_45",
        "P1L1__ud_patch ns1",
        "P1L1__ud",
        "P1L1__core",
        "P1L1__ud.2",
        "P1L1__woven_45.2",
    ]
    five_layers = ["P1L1__woven_45", "P1L1__ud", "P1L1__core", "P1L1__ud.2", "P1L1__woven_45.2"]

    assert plies_by_element[0] == six_layers
    assert plies_by_element[1] == six_layers
    assert plies_by_element[2] == five_layers
    assert plies_by_element[3] == five_layers
