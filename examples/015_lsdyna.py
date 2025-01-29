import ansys.dpf.core as dpf
from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.data_sources import ContinuousFiberCompositesFiles, CompositeDefinitionFiles
from ansys.dpf.core import DataSources, Operator, unit_systems

from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data

from ansys.dpf.composites.constants import Spot, Sym3x3TensorComponent

import os
import json

server = connect_to_or_start_server(ansys_path=r'D:\ANSYSDev\dpf_composites\fake_wb_installation')

solver_dir = r'D:\ANSYSDev\dpf_composites\test_data\lsdyna\shell_model_2'

composite_files = ContinuousFiberCompositesFiles(
    files_are_local=True,
    rst=[os.path.join(solver_dir, 'd3plot')],
    composite={"shell": CompositeDefinitionFiles(
        mapping=None,
        definition=os.path.join(solver_dir, 'ACPCompositeDefinitions.h5'),
    )
    },
    engineering_data=os.path.join(solver_dir, 'material.engd'),
    solver_input_file=os.path.join(solver_dir, 'input.k')
)

composite_model = CompositeModel(
    composite_files=composite_files,
    server=server,
    default_unit_system=unit_systems.solver_nmm
)

element_info_1 = composite_model.get_element_info(1)
element_info_2 = composite_model.get_element_info(2)
print(element_info_1)
print(element_info_2)


stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Prepare data
# ~~~~~~~~~~~~
# The LS Dyna results have to be pre-processed to support
# filtering and in order make them consistent with the layup
# model.

keyword_parser = Operator("composite::ls_dyna_keyword_parser")
keyword_parser.inputs.data_sources(composite_model.data_sources.solver_input_file)
keyword_parser.inputs.keyword("DATABASE_EXTENT_BINARY")
keyword_options_as_json = json.loads(keyword_parser.outputs[0].get_data())

stress_container = stress_operator.get_output(
    pin=0, output_type=dpf.types.fields_container
)
strip_operator = Operator("composite::ls_dyna_strip_results")
strip_operator.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator.inputs.fields_container(stress_container)
strip_operator.inputs.mesh(composite_model.get_mesh())

stripped_stress_field = strip_operator.get_output(
    pin=0, output_type=dpf.types.fields_container
)[0]


# stress_field_material_coord = stress_operator.get_output(
#     pin=0, output_type=dpf.types.fields_container
# )[0]

# %%
# Filter data by analysis ply
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~

# %%
# List all available analysis plies.
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
all_ply_names

for ply_name in all_ply_names:
    print(f"Plotting ply {ply_name}")
    elemental_values = get_ply_wise_data(
        field=stripped_stress_field,
        ply_name=ply_name,
        mesh=composite_model.get_mesh(),
        component=Sym3x3TensorComponent.TENSOR11,
        spot_reduction_strategy=SpotReductionStrategy.AVG,
        requested_location=dpf.locations.elemental,
    )

    composite_model.get_mesh().plot(elemental_values)
