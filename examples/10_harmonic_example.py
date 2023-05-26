import ansys.dpf.core as dpf
import matplotlib.pyplot as plt
import numpy as np

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    MaxStressCriterion,
    TsaiWuCriterion,
)
from ansys.dpf.composites.layup_info.material_operators import get_material_operators
from ansys.dpf.composites.select_indices import get_selected_indices
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.unit_system import get_unit_system

# Start the server. By default this starts
# a new local server and loads the composites plugin
server = connect_to_or_start_server(port=50052)

# Read Workbench modal model
result_folder = r"D:\ANSYSDev\wb_projects\composite_harmonic_files\dp0\SYS-1\MECH"
composite_files = get_composite_files_from_workbench_result_folder(result_folder)
composite_model = CompositeModel(composite_files, server)

# Read material data

# Read mesh
mesh_provider = composite_model.core_model.metadata.mesh_provider

# Set time scoping
tf = composite_model.core_model.metadata.time_freq_support
frequencies = tf.time_frequencies.data
time_ids = list(range(1, tf.n_sets + 1))

# Failure Criteria
combined_fc = CombinedFailureCriterion(
    name="My Failure Criteria",
    failure_criteria=[
        MaxStressCriterion(),
        TsaiWuCriterion(),
    ],
)

## Actual script

# Stress & strains real & imaginary at all frequencies
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)
stress_operator.inputs.time_scoping.connect(time_ids)
stress_field = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)

strain_operator = composite_model.core_model.results.elastic_strain()
strain_operator.inputs.bool_rotate_to_global(False)
strain_operator.inputs.time_scoping.connect(time_ids)
strain_field = strain_operator.get_output(pin=0, output_type=dpf.types.fields_container)

# Sweeping phase with 10 degrees increment
sweepphases = range(-180, 180, 10)
failure_index = np.zeros((len(sweepphases), int(tf.n_sets)))
phase_index = 0

f_sweepingphases = dpf.FieldsContainer()
f_sweepingphases.labels = ["time", "sweepphase"]

for x in sweepphases:
    # Stress & strains at sweeping phase x

    Stress_phase = dpf.operators.math.sweeping_phase_fc(
        fields_container=stress_field, angle=float(x), unit_name="deg", abs_value=False
    )

    Strain_phase = dpf.operators.math.sweeping_phase_fc(
        fields_container=strain_field, angle=float(x), unit_name="deg", abs_value=False
    )

    # Max f (f=actual stress/failure stress) per element of TsaiWu and MaxStress criterion

    material_operators = get_material_operators(
        composite_model.data_sources.rst,
        composite_model.data_sources.engineering_data,
        get_unit_system(composite_model.data_sources.rst),
    )
    failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
    failure_evaluator.inputs.configuration(combined_fc.to_json())
    failure_evaluator.inputs.materials_container(material_operators.material_provider.outputs)
    failure_evaluator.inputs.stresses_container(Stress_phase.outputs.fields_container())
    failure_evaluator.inputs.strains_container(Strain_phase.outputs.fields_container())
    failure_evaluator.inputs.mesh(composite_model.get_mesh())

    minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
    minmax_per_element.inputs.fields_container(failure_evaluator.outputs.fields_container)
    minmax_per_element.inputs.mesh(mesh_provider.outputs.mesh)
    minmax_per_element.inputs.material_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )

    output = minmax_per_element.outputs.field_max()

    for i in range(1, tf.n_sets + 1):
        dict_field = {"time": i, "sweepphase": x}
        f_sweepingphases.add_field(dict_field, output.get_field({"failure_label": 1, "time": i}))

# Max over all sweepingphases and frequencies. Plot result
op_f_max_over_freq_all_sweepphases = (
    dpf.operators.min_max.min_max_by_entity()
)  # operator instantiation
op_f_max_over_freq_all_sweepphases.inputs.fields_container.connect(f_sweepingphases)
f_max_over_freq_all_sweepphases = op_f_max_over_freq_all_sweepphases.outputs.field_max()

composite_model.core_model.metadata.meshed_region.plot(f_max_over_freq_all_sweepphases)


# Critical element
index_max = f_max_over_freq_all_sweepphases.data_as_list.index(
    f_max_over_freq_all_sweepphases.data.max()
)
id_max = f_max_over_freq_all_sweepphases.scoping.ids[index_max]
print("The element with highest IRF is " + str(id_max))
ScopingMax = dpf.Scoping()
ScopingMax.location = "Elemental"
ScopingMax.ids = [id_max]

# Scoping on critical element and max over sweepingphases
op_f_CritElem = dpf.operators.scoping.rescope_fc()  # operator instantiation
op_f_CritElem.inputs.fields_container.connect(f_sweepingphases)
op_f_CritElem.inputs.mesh_scoping.connect(ScopingMax)
f_CritElem = op_f_CritElem.outputs.fields_container()

op_f_CritElem_OverSweeping = dpf.operators.min_max.min_max_over_label_fc()
op_f_CritElem_OverSweeping.inputs.fields_container.connect(f_CritElem)
op_f_CritElem_OverSweeping.inputs.label.connect("time")
f_CritElem_OverSweeping = op_f_CritElem_OverSweeping.outputs.field_max()

fig, axs = plt.subplots(1)
fig.suptitle(
    "Frequency response curve of max IRF in all layers in element "
    + str(id_max)
    + " using MaxStress & TsaiWu at 10 degrees sweep"
)
axs.plot(frequencies, f_CritElem_OverSweeping.data_as_list)

index_highest_IRF = f_CritElem_OverSweeping.data_as_list.index(
    max(f_CritElem_OverSweeping.data_as_list)
)
sweeps_critical = op_f_CritElem_OverSweeping.outputs.domain_ids_max()
sweep_critical_max_IRF = sweeps_critical[index_highest_IRF]
print("Sweeping phase critical at frequency with highest IRF is " + str(sweep_critical_max_IRF))

# Now we are going to identify the critical layer of critical element

stress_operator.inputs.mesh_scoping.connect(ScopingMax)
stress_field = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)
strain_operator.inputs.mesh_scoping.connect(ScopingMax)
strain_field = strain_operator.get_output(pin=0, output_type=dpf.types.fields_container)

Stress_phase = dpf.operators.math.sweeping_phase_fc(
    fields_container=stress_field,
    angle=float(sweep_critical_max_IRF),
    unit_name="deg",
    abs_value=False,
)

Strain_phase = dpf.operators.math.sweeping_phase_fc(
    fields_container=strain_field,
    angle=float(sweep_critical_max_IRF),
    unit_name="deg",
    abs_value=False,
)

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.inputs.configuration(combined_fc.to_json())
failure_evaluator.inputs.materials_container(material_operators.material_provider.outputs)
failure_evaluator.inputs.stresses_container(Stress_phase.outputs.fields_container())
failure_evaluator.inputs.strains_container(Strain_phase.outputs.fields_container())
failure_evaluator.inputs.mesh(composite_model.get_mesh())

failure_ElemCrit = failure_evaluator.outputs.fields_container()
time_critical = index_highest_IRF + 1
field_time_critical = failure_ElemCrit.get_field({"failure_label": 1, "time": time_critical})

indices_critical = field_time_critical.data_as_list.index(max(field_time_critical.data_as_list))

element_info = composite_model.get_element_info(id_max)

for LayerId in range(element_info.n_layers):
    selected_indices = get_selected_indices(element_info, layers=[LayerId])
    layer_name = composite_model.get_analysis_plies(id_max)[LayerId]
    if indices_critical in selected_indices:
        print("Critical layer is " + str(layer_name))
        print("Maximum IRF is " + str(field_time_critical.max().data[0]))
