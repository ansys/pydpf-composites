import ansys.dpf.core as dpf
from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.data_sources import ContinuousFiberCompositesFiles, CompositeDefinitionFiles
from ansys.dpf.core import Operator, unit_systems

from ansys.dpf.composites.layup_info import AnalysisPlyInfoProvider, get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data

from ansys.dpf.composites.constants import Spot, Sym3x3TensorComponent

import os
import json

#server = connect_to_or_start_server(port=50055)
#server = connect_to_or_start_server(ansys_path=r'D:\ANSYSDev\dpf_composites\fake_WB_installation')
server = connect_to_or_start_server(ansys_path=r'C:\Program Files\ANSYS Inc\v252')

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
strip_operator = Operator("composite::ls_dyna_preparing_results")
strip_operator.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator.inputs.fields_container(stress_container)
strip_operator.inputs.mesh(composite_model.get_mesh())

stripped_stress_field = strip_operator.get_output(
    pin=0, output_type=dpf.types.fields_container
)[-1]

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
    # todo: enable again
    # composite_model.get_mesh().plot(elemental_values)

# %%
# Plot history variables
# ~~~~~~~~~~~~~~~~~~~~~~
time_freq_support = composite_model.core_model.metadata.time_freq_support
time_freq_support.time_frequencies.data


hv_operator = dpf.Operator("lsdyna::d3plot::history_var")
hv_operator.inputs.data_sources(composite_model.data_sources.rst)
hv_operator.inputs.time_scoping(list(time_freq_support.time_frequencies.data))

hv_container = hv_operator.outputs.history_var.get_data()
print(hv_container.labels)

strip_operator_hv = Operator("composite::ls_dyna_preparing_results")
strip_operator_hv.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator_hv.inputs.mesh(composite_model.get_mesh())
strip_operator_hv.inputs.fields_container(hv_container)
stripped_hv_container = strip_operator_hv.get_output(
    pin=0, output_type=dpf.types.fields_container
)

stripped_hv_field = stripped_hv_container.get_field({"time":-1, "ihv":13})

for ply_name in all_ply_names:
    print(f"Plotting ply {ply_name}")
    elemental_values = get_ply_wise_data(
        field=stripped_hv_field,
        ply_name=ply_name,
        mesh=composite_model.get_mesh(),
        component=0,
        spot_reduction_strategy=SpotReductionStrategy.MAX,
        requested_location=dpf.locations.elemental,
    )

    composite_model.get_mesh().plot(elemental_values)
