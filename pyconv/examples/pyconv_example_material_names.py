"""
This example shows how to extract stresses from a stress field and filter them
by material name and comoponent. The example uses the composite model to get the stress field.
It also uses the composite model to get the material names and their corresponding
DPF material IDs. The example then uses the select_indices module to get the indices
of the stresses of a certain material. Finally, the example plots the maximum stresses.
"""

import ansys.dpf.core as dpf
import numpy as np

# import modules from pyDPF Composites
from ansys.dpf.composites.composite_model import CompositeModel

# import the stress component enum
from ansys.dpf.composites.constants import Sym3x3TensorComponent
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder

# the select_indices module can be used to extract indices by different criteria.
# For example, layer index, ply name, node index, spot, etc.
from ansys.dpf.composites.select_indices import get_selected_indices_by_dpf_material_ids
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# ansys.dpf.composites requires a running DPF server where the composites plugin is loaded.
# this is achieved by calling connect_to_or_start_server() from the server_helpers module.
server = connect_to_or_start_server()

# Define path to new Workbench result folder
result_folder = "D:/tmp/ger89_files/dp0/SYS-2/MECH"
# Get composite files from Workbench result folder
composite_files = get_composite_files_from_workbench_result_folder(result_folder)

# Create a composite model with new files
composite_model = CompositeModel(composite_files, server)

# store the dpf material id of the material named Epoxy_Carbon_UD_230GPa_Prepreg
# to a variable to use it for the filtering.
epoxy_dpf_material_id = composite_model.material_names["Epoxy_Carbon_UD_230GPa_Prepreg"]

# get the stress field of the first time step
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_field = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)[0]

# store the stress components for the filtering
comp_s13 = Sym3x3TensorComponent.TENSOR31  # interlaminar shear stress s13
comp_s23 = Sym3x3TensorComponent.TENSOR32  # interlaminar shear stress s23
comp_s33 = Sym3x3TensorComponent.TENSOR33  # interlaminar normal stress s3

# generate a new field which contains only the maximum of the interlaminar stresses, so maximum
# s13, s23 and s3.
stresses_epoxy = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
with stresses_epoxy.as_local_field() as local_result_field:
    element_ids = stress_field.scoping.ids

    for element_id in element_ids:
        # get all element information such as number of layers, material IDs etc.
        element_info = composite_model.get_element_info(element_id)
        assert element_info is not None
        # get the indices for the filtering of data. In this case, the indices
        # are selectecd by the DPF material ID.
        selected_indices = get_selected_indices_by_dpf_material_ids(
            element_info, [epoxy_dpf_material_id]
        )

        if selected_indices.any():
            # get the stresses of one element
            stress_data = stress_field.get_entity_data_by_id(element_id)[selected_indices]
            # get the stresses for a list of components and compute the maximum
            maxima = [
                np.max(stress_data[:, comp_s13]),
                np.max(stress_data[:, comp_s23]),
                np.max(stress_data[:, comp_s33]),
            ]
            # store the overall maximum and the element id in the result field
            local_result_field.append([np.max(maxima)], element_id)

# plot the generated field
composite_model.get_mesh().plot(stresses_epoxy)
