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

"""
.. _lsdyna_bird_strike:

LS-Dyna Bird Strike
-------------------

This example shows how to post-process a LS-Dyna analysis.
And how to access ply-wise results. The simulation mimics
a bird strike on a leading edge of a composite wing.

The additional steps are required to post-process LS-Dyna results
if compared with a Mechanical APDL analysis.
Pre-processing:
 - The input file must be generated with WB LS Dyna
 - In WB Mechanical, enable the beta options and ``Output Integration
   Points Results for All ACP Plies`` or manually set MAXINT of the keyword
   ``DATABASE_EXTENT_BINARY`` to the maximum number of plies.
Post-processing:
 - The solver input file (keyword file) has to be passed to the composite model
   and set the solver_type of ContinuousFiberCompositesFiles to ``LSDYNA``.
 - The number of maximum integration points (MAXINT) has to be extracted from
   the keyword file. See ``composite::ls_dyna_keyword_parser`` operator.
 - The results (stress, strain, history variable etc.) have to be
   pre-processed to support ply-wise filtering and to make them consistent.
   See ``composite::ls_dyna_preparing_results`` operator.
"""

# %%
# Set up analysis
# ~~~~~~~~~~~~~~~
# Setup of the analysis and initialize the composite model.
import json

import ansys.dpf.core as dpf
from ansys.dpf.core import Operator, unit_systems

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import Sym3x3TensorComponent
from ansys.dpf.composites.example_helper import get_continuous_fiber_example_files
from ansys.dpf.composites.layup_info import get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.server_helpers import connect_to_or_start_server

# sphinx_gallery_thumbnail_number = 3

server = connect_to_or_start_server(ansys_path=r"C:\Program Files\ANSYS Inc\v252")
composite_files_on_server = get_continuous_fiber_example_files(server, "lsdyna_bird_strike")

composite_model = CompositeModel(
    composite_files=composite_files_on_server,
    server=server,
    default_unit_system=unit_systems.solver_nmm,
)

# %%
# Get all the time ids and displacement at the final time step
time_freq_support = composite_model.core_model.metadata.time_freq_support
time_ids = [v for v in time_freq_support.time_frequencies.scoping.ids]

# %%
# Get displacement at the final time step
disp_result = composite_model.core_model.results.displacement()
displacement = disp_result.eval().get_field({"time": time_ids[-1]})

# %%
# Read stresses in the material coordinate system
stress_operator = composite_model.core_model.results.stress()
stress_operator.inputs.bool_rotate_to_global(False)

# %%
# Prepare data
# ~~~~~~~~~~~~
# The LS Dyna results have to be pre-processed to support ply-wise
# filtering. The data must be consistent with the layup
# model. This requires the extraction of the number of maximum
# integration points (MAXINT) from the DATABASE_EXTENT_BINARY keyword.
# Parameters can be read from the input file using the keyword parser
# operator as shown here.
keyword_parser = Operator("composite::ls_dyna_keyword_parser")
keyword_parser.inputs.data_sources(composite_model.data_sources.solver_input_file)
keyword_parser.inputs.keyword("DATABASE_EXTENT_BINARY")
keyword_options_as_json = json.loads(keyword_parser.outputs[0].get_data())

# %%
# Strip the stress container (remove unneeded integration point results)
stress_container = stress_operator.outputs.fields_container.get_data()
strip_operator = Operator("composite::ls_dyna_preparing_results")
strip_operator.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator.inputs.fields_container(stress_container)
strip_operator.inputs.mesh(composite_model.get_mesh())
stripped_stress_container = strip_operator.outputs.fields_container.get_data()

# %%
# Filter data by analysis ply
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Print stresses of a few plies at the last time step
stripped_stress_field = stripped_stress_container.get_field({"time": time_ids[-1]})
all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
print(all_ply_names)

for ply_name in ["P2L1__ModelingPly.1", "P2L1__ModelingPly.2"]:
    print(f"Plotting s1 of ply {ply_name}")
    elemental_values = get_ply_wise_data(
        field=stripped_stress_field,
        ply_name=ply_name,
        mesh=composite_model.get_mesh(),
        component=Sym3x3TensorComponent.TENSOR11,
        spot_reduction_strategy=SpotReductionStrategy.MAX,
        requested_location=dpf.locations.elemental,
    )

    composite_model.get_mesh().plot(
        field_or_fields_container=elemental_values, deform_by=displacement
    )


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
hv_field = hv_container.get_field({"time": time_ids[-1], "ihv": 2})

strip_operator_hv = Operator("composite::ls_dyna_preparing_results")
strip_operator_hv.inputs.maxint(int(keyword_options_as_json["maxint"]))
strip_operator_hv.inputs.mesh(composite_model.get_mesh())
strip_operator_hv.inputs.fields_container(hv_container)
stripped_hv_container = strip_operator_hv.outputs.fields_container.get_data()

stripped_hv_field = stripped_hv_container.get_field({"time": time_ids[-1], "ihv": 2})

# todo: use 3 images as thumbnail
for ply_name in ["P2L1__ModelingPly.1", "P2L1__ModelingPly.2"]:
    print(f"Plotting history variable 2 of ply {ply_name}")
    elemental_values = get_ply_wise_data(
        field=stripped_hv_field,
        ply_name=ply_name,
        mesh=composite_model.get_mesh(),
        component=0,
        spot_reduction_strategy=SpotReductionStrategy.MAX,
        requested_location=dpf.locations.elemental,
    )

    composite_model.get_mesh().plot(
        field_or_fields_container=elemental_values, deform_by=displacement
    )
