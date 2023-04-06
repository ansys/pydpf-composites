import ansys.dpf.core as dpf
import numpy as np
from scipy.spatial.transform import Rotation

from ansys.dpf.composites.example_helper import get_short_fiber_example_files
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

a11_name = "Orientation Tensor A11"
a22_name = "Orientation Tensor A22"

for name, server_kwargs in [("local", {}), ("container", {"port": 21002})]:
    server = connect_to_or_start_server(**server_kwargs)
    composite_files_on_server = get_short_fiber_example_files(server, "short_fiber")

    data_sources = dpf.DataSources()
    data_sources.add_file_path(composite_files_on_server.dsdat, "dat")
    data_sources.set_result_file_path(composite_files_on_server.rst)

    model = dpf.Model(data_sources=data_sources)
    mesh = model.metadata.meshed_region

    field_variable_provider = dpf.Operator("composite::inistate_field_variables_provider")
    field_variable_provider.inputs.data_sources(data_sources)
    field_variable_provider.inputs.mesh(model.metadata.mesh_provider)

    field_variables = field_variable_provider.outputs.fields_container.get_data()

    field_variable_dict = {}
    for field_variable in field_variables:
        field_variable_dict[field_variable.name] = field_variable

    element_ids = field_variables[0].scoping.ids

    fiber_orientation_tensor = dpf.fields_factory.create_tensor_field(
        num_entities=len(element_ids), location=dpf.locations.elemental
    )

    ele_orientation_op = dpf.operators.result.element_orientations(
        data_sources=data_sources, requested_location="Elemental", bool_rotate_to_global=False
    )

    euler_angles_field = ele_orientation_op.outputs.fields_container()[0]
    for eid in element_ids:
        V = Rotation.from_euler(
            seq="ZXY", angles=euler_angles_field.get_entity_data_by_id(eid)[0], degrees=True
        ).as_matrix()
        d1 = field_variable_dict[a11_name].get_entity_data_by_id(eid)[0]
        d2 = field_variable_dict[a22_name].get_entity_data_by_id(eid)[0]
        D = np.diag([d1, d2, max(1.0 - d1 - d2, 0.0)])
        aRot = np.matmul(np.matmul(V, D), V.transpose())
        fiber_orientation_tensor.append(
            [aRot[0, 0], aRot[1, 1], aRot[2, 2], aRot[0, 1], aRot[1, 2], aRot[0, 2]], eid
        )

    fiber_orientation_tensor_fc = dpf.operators.utility.field_to_fc(
        field=fiber_orientation_tensor
    ).outputs.fields_container()

    aXX = fiber_orientation_tensor_fc.select_component(0)[0]

    print(f"Result {name}: ", aXX.data[0])
