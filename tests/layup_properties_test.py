from ansys.dpf.core import Operator
import pytest

from ansys.dpf.composites.data_sources import get_composites_data_sources
from ansys.dpf.composites.example_helper import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.layup_info import LayupPropertiesProvider, add_layup_info_to_mesh
from ansys.dpf.composites.layup_info.material_operators import get_material_operators

from .helper import get_basic_shell_files


def test_layup_properties(dpf_server):
    files = get_basic_shell_files()
    if not dpf_server.local_server:
        server_files = upload_continuous_fiber_composite_files_to_server(files, dpf_server)

    composite_data_sources = get_composites_data_sources(server_files)
    mesh_provider = Operator("MeshProvider")
    mesh_provider.inputs.data_sources(composite_data_sources.rst)
    mesh = mesh_provider.outputs.mesh()

    material_operators = get_material_operators(
        composite_data_sources.rst, composite_data_sources.engineering_data
    )
    layup_provider = add_layup_info_to_mesh(
        composite_data_sources, mesh=mesh, material_operators=material_operators
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
