"""
.. _interlaminar_normal_stress_example:

Interlaminar Normal Stresses in Layered Shells
----------------------------------------------

This example shows how to connect the different dpf operators that are needed to
evaluate the interlaminar normal stresses, in short INS, in layered shells.
For simple use cases it is preferable to use the composite failure operator
(:ref:`sphx_glr_examples_gallery_examples_failure_operator_example.py`)
or the composite sampling point operator
(:ref:`sphx_glr_examples_gallery_examples_sampling_point_operator_example.py`).
The :ref:`sphx_glr_examples_gallery_examples_filter_composite_data_example.py` example shows how
helper functions can be used to obtain composite result data.

INS are typically not available if layered shell elements are
used. The INS operator recomputes s3 based on the laminate strains, the geometrical curvature and
the lay-up.

The input of the INS operator are strains, stresses, material data, and lay-up data.
Note, the INS operator fills the results directly into the stress field.
"""

#%%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites import get_element_info_provider, get_selected_indices
from ansys.dpf.composites.add_layup_info_to_mesh import (
    add_layup_info_to_mesh,
    get_composites_data_sources,
)
from ansys.dpf.composites.enums import Sym3x3TensorComponent
from ansys.dpf.composites.example_helper.example_helper import (
    connect_to_or_start_server,
    get_continuous_fiber_example_files,
)

server_context = connect_to_or_start_server()
composite_files_on_server = get_continuous_fiber_example_files(server_context, "ins")

#%%

model = dpf.Model(composite_files_on_server.rst)
rst_data_source = dpf.DataSources(composite_files_on_server.rst)

eng_data_source = dpf.DataSources()
eng_data_source.add_file_path(composite_files_on_server.engineering_data, "EngineeringData")

composite_definitions_source = dpf.DataSources()
composite_definitions_source.add_file_path(
    composite_files_on_server.composite_definitions, "CompositeDefinitions"
)

#%%
# Setup Mesh Provider
mesh_provider = model.metadata.mesh_provider

#%%
# Set up material and lay-up provider
composites_data_sources = get_composites_data_sources(composite_files_on_server)
layup_operators = add_layup_info_to_mesh(
    mesh=mesh_provider.outputs.mesh(), data_sources=composites_data_sources
)

layup_provider = layup_operators.layup_provider
material_provider = layup_operators.material_operators.material_provider

#%%
# Setup the result operators: strains and stresses
# Rotate to global is False because the post-processing engine expects the results to be
# in the element coordinate system ( material coordinate system)

strain_operator = dpf.Operator("EPEL")
strain_operator.inputs.data_sources(rst_data_source)
strain_operator.inputs.bool_rotate_to_global(False)

stress_operator = dpf.Operator("S")
stress_operator.inputs.data_sources(rst_data_source)
stress_operator.inputs.bool_rotate_to_global(False)

#%%
# Setup of failure evaluator. Combines the results and evaluates all the failure criteria.
# The output contains the maximum failure criteria for each integration point.
#

ins_operator = dpf.Operator("composite::interlaminar_normal_stress_operator")
ins_operator.inputs.materials_container(material_provider.outputs)
ins_operator.inputs.mesh(mesh_provider.outputs.mesh)
ins_operator.inputs.mesh_properties_container(layup_provider.outputs.mesh_properties_container)
# pass inputs by pin because the input name is not set yet
ins_operator.connect(24, layup_provider.outputs.section_data_container)
ins_operator.connect(0, strain_operator.outputs.fields_container)
ins_operator.connect(1, stress_operator.outputs.fields_container)

# call run because ins operator has not output
ins_operator.run()

#%%
# Get element infos for all the elements
stress_field = stress_operator.outputs.fields_container[0]
element_info_provider = get_element_info_provider(mesh_provider.outputs.mesh, rst_data_source)
element_ids = stress_field.scoping.ids
element_infos = [element_info_provider.get_element_info(element_id) for element_id in element_ids]

#%%
# Plot max interlaminar normal stresses for each element

s3_component = Sym3x3TensorComponent.tensor33
result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with result_field.as_local_field() as local_result_field:
    element_ids = stress_field.scoping.ids
    for element_id in element_ids:
        stress_data = stress_field.get_entity_data_by_id(element_id)
        element_info = element_info_provider.get_element_info(element_id)
        assert element_info is not None
        # select all stresses from bottom to top of node 0
        selected_indices = get_selected_indices(element_info, layers=None, nodes=[0], spots=None)

        s3 = stress_data[selected_indices][:: s3_component.value]
        local_result_field.append(max(s3), element_id)

mesh = mesh_provider.outputs.mesh()
mesh.plot(result_field)
