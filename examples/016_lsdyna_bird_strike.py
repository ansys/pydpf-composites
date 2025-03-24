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

#server = connect_to_or_start_server(ansys_path=r'D:\ANSYSDev\dpf_composites\fake_WB_installation')
server = connect_to_or_start_server(ansys_path=r'C:\Program Files\ANSYS Inc\v252')

solver_dir = r'D:\tmp\SPH_CompositeWing_25R2_files\dp0\SYS-4\MECH'

composite_files = ContinuousFiberCompositesFiles(
    files_are_local=True,
    rst=[os.path.join(solver_dir, 'd3plot')],
    composite={"shell": CompositeDefinitionFiles(
        mapping=None,
        definition=os.path.join(solver_dir, 'Setup 3', 'ACPCompositeDefinitions.h5'),
    )
    },
    engineering_data=os.path.join(solver_dir, 'MatML.xml'),
    solver_input_file=os.path.join(solver_dir, 'input.k')
)

composite_model = CompositeModel(
    composite_files=composite_files,
    server=server,
    default_unit_system=unit_systems.solver_nmm
)

time_freq_support = composite_model.core_model.metadata.time_freq_support
time_ids = [v for v in time_freq_support.time_frequencies.scoping.ids]

stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Prepare data
# ~~~~~~~~~~~~
# The LS Dyna results have to be pre-processed to support ply-wise
# filtering and in order make them consistent with the layup
# model. This requires the extraction of the number of maximum
# integration points (MAXINT) from the DATABASE_EXTENT_BINARY keyword.
# Parameters can be read from the input file using the keyword parser
# operator.
keyword_parser = Operator("composite::ls_dyna_keyword_parser")
keyword_parser.inputs.data_sources(composite_model.data_sources.solver_input_file)
keyword_parser.inputs.keyword("DATABASE_EXTENT_BINARY")
keyword_options_as_json = json.loads(keyword_parser.outputs[0].get_data())

stress_container = stress_operator.outputs.fields_container.get_data()
strip_operator = Operator("composite::ls_dyna_preparing_results")
strip_operator.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator.inputs.fields_container(stress_container)
strip_operator.inputs.mesh(composite_model.get_mesh())
stripped_stress_container = strip_operator.outputs.fields_container.get_data()
stripped_stress_field = stripped_stress_container.get_field({"time":time_ids[-1]})

# %%
# Filter data by analysis ply
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Print stresses of a few plies at the last time step
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
print(all_ply_names)

for ply_name in ["P2L1__ModelingPly.1", "P2L2__ModelingPly.1"]:
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


# %%
# Plot history variables
# ~~~~~~~~~~~~~~~~~~~~~~
# The same procedure can be applied to history variables.
# In this example, the 2nd history variable (compressive fiber mode)
# is plotted. 1 stands for elastic, 0 means failed.
hv_operator = dpf.Operator("lsdyna::d3plot::history_var")
hv_operator.inputs.data_sources(composite_model.data_sources.rst)
hv_operator.inputs.time_scoping(time_ids)

hv_container = hv_operator.outputs.history_var.get_data()
print(hv_container.labels)
hv_field = hv_container.get_field({"time":time_ids[-1], "ihv":2})

strip_operator_hv = Operator("composite::ls_dyna_preparing_results")
strip_operator_hv.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator_hv.inputs.mesh(composite_model.get_mesh())
strip_operator_hv.inputs.fields_container(hv_container)
stripped_hv_container = strip_operator_hv.outputs.fields_container.get_data()

stripped_hv_field = stripped_hv_container.get_field({"time":time_ids[-1], "ihv":2})

for ply_name in ["P2L1__ModelingPly.1", "P2L2__ModelingPly.1"]:
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
