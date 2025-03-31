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

import json
import pathlib

import ansys.dpf.core as dpf
from ansys.dpf.core import Operator, unit_systems
import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import (
    D3PLOT_KEY_AND_FILENAME,
    SolverType,
    Sym3x3TensorComponent,
)
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.layup_info import get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.server_helpers import version_older_than


def test_composite_model_and_ply_wise_filtering(dpf_server):
    """
    Verify that the composite model can be initialized and element info,
    filtering by ply for stresses and history variables works as expected.
    """
    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Post-processing of LSDyna solutions requires DPF server 10.0 or later.")

    test_data_dir = pathlib.Path(__file__).parent / "data" / "lsdyna" / "basic_shell_model"

    composite_files = get_composite_files_from_workbench_result_folder(
        result_folder=test_data_dir,
        ensure_composite_definitions_found=True,
        solver_type=SolverType.LSDYNA,
    )

    assert str(composite_files.solver_input_file).endswith("input.k")
    assert len(composite_files.result_files) == 1
    assert str(composite_files.result_files[0]).endswith(D3PLOT_KEY_AND_FILENAME)
    assert composite_files.solver_type == SolverType.LSDYNA

    composite_model = CompositeModel(
        composite_files=composite_files,
        server=dpf_server,
        default_unit_system=unit_systems.solver_nmm,
    )

    # verify that the element info can be created
    element_info_1 = composite_model.get_element_info(1)
    assert element_info_1.id == 1
    assert element_info_1.element_type == 15
    assert element_info_1.n_layers == 5
    assert element_info_1.n_corner_nodes == 3
    assert element_info_1.n_spots == 1
    assert element_info_1.is_layered == True
    assert element_info_1.is_shell == True
    assert element_info_1.number_of_nodes_per_spot_plane == 1
    assert np.all(element_info_1.dpf_material_ids == np.array([1, 1, 3, 1, 1]))

    # Filter data by analysis ply name
    all_ply_names = get_all_analysis_ply_names(composite_model.get_mesh())
    assert (
        all_ply_names.sort()
        == [
            "P1L1__ModelingPly.1",
            "P1L1__ModelingPly.9",
            "P1L1__ModelingPly.8",
            "P1L1__ModelingPly.7",
            "P1L1__ModelingPly.6",
            "P1L1__ModelingPly.5",
        ].sort()
    )

    # Verify that the results are loaded as expected (all time steps)
    time_freq_support = composite_model.core_model.metadata.time_freq_support
    time_ids = [int(v) for v in time_freq_support.time_frequencies.scoping.ids]
    assert time_ids == [v for v in range(1, 23)]

    # Verify that the stresses can be stripped and filtered by ply
    stress_operator = composite_model.core_model.results.stress()
    stress_operator.inputs.bool_rotate_to_global(False)

    keyword_parser = Operator("composite::ls_dyna_keyword_parser")
    keyword_parser.inputs.data_sources(composite_model.data_sources.solver_input_file)
    keyword_parser.inputs.keyword("DATABASE_EXTENT_BINARY")
    keyword_options_as_json = json.loads(keyword_parser.outputs.keyword_options.get_data())

    maxint = int(keyword_options_as_json["maxint"])
    assert maxint == 6

    stress_container = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)
    strip_operator = Operator("composite::ls_dyna_preparing_results")
    strip_operator.inputs.maxint(maxint)
    strip_operator.inputs.fields_container(stress_container)
    strip_operator.inputs.mesh(composite_model.get_mesh())

    stripped_stress_container = strip_operator.outputs.fields_container.get_data()

    stripped_stress_field = stripped_stress_container.get_field_by_time_id(22)

    # load step 22 of 22
    ref_stresses = {
        "P1L1__ModelingPly.1": {
            19: 7.66085446e-01,  # IP 1 (1-index) compared with LS PrepPost
            48: 7.08469152e-01,  # IP 1 (1-index) compared with LS PrePost
        },
        "P1L1__ModelingPly.7": {
            19: 56.47654724,  # IP 4 (1-index) compared with LS PrepPost
            48: 39.02941895,  # IP 4 (1-index) compared with LS PrepPost
            52: 200.83200073242188,  # IP 3 (1-index) compared with LS PrepPost
            133: 232.65634155273438,  # IP 3 (1-index) compared with LS PrepPost
        },
    }

    for ply_name, ref_values in ref_stresses.items():
        print(f"Comparing stresses of {ply_name}")

        elemental_values = get_ply_wise_data(
            field=stripped_stress_field,
            ply_name=ply_name,
            mesh=composite_model.get_mesh(),
            component=Sym3x3TensorComponent.TENSOR11,
            spot_reduction_strategy=SpotReductionStrategy.MAX,
            requested_location=dpf.locations.elemental,
        )

        for id, ref_value in ref_stresses[ply_name].items():
            # print(f"Comparing elemental stress of id {id}")
            current = elemental_values.get_entity_data_by_id(id)
            # print(f"{id}: {ref_value} vs {current}")
            np.testing.assert_almost_equal(
                current[0],
                ref_value,
                err_msg=f"Elemental stress of id {id} does not match. Ply {ply_name}",
            )

    # verify that data extraction also works for history variables
    hv_operator = dpf.Operator("lsdyna::d3plot::history_var")
    hv_operator.inputs.data_sources(composite_model.data_sources.result_files)
    hv_operator.inputs.time_scoping(time_ids)

    hv_container = hv_operator.outputs.history_var.get_data()

    strip_operator_hv = Operator("composite::ls_dyna_preparing_results")
    strip_operator_hv.inputs.maxint(int(keyword_options_as_json["maxint"]))
    strip_operator_hv.inputs.mesh(composite_model.get_mesh())
    strip_operator_hv.inputs.fields_container(hv_container)
    stripped_hv_container = strip_operator_hv.outputs.fields_container.get_data()

    stripped_hv_field = stripped_hv_container.get_field({"time": time_ids[-1], "ihv": 13})

    ref_hv_values = {
        #  compared with LS PrePost
        "P1L1__ModelingPly.1": {
            19: 57.83656692504883,  # IP 1 (1-based)
            48: 103.61775207519531,  # IP 1 (1-based)
        },
        #  compared with LS PrePost
        "P1L1__ModelingPly.7": {
            19: 627.0761108398438,  # IP 4 (1-based)
            48: 810.4426879882812,  # IP 4 (1-based)
            52: 714.7772827148438,  # IP 3 (1-based)
            133: 671.97705078125,  # IP 3 (1-based)
        },
    }

    for ply_name, ref_values in ref_hv_values.items():
        print(f"Plotting history variable 2 of ply {ply_name}")
        elemental_values = get_ply_wise_data(
            field=stripped_hv_field,
            ply_name=ply_name,
            mesh=composite_model.get_mesh(),
            component=0,
            spot_reduction_strategy=SpotReductionStrategy.MAX,
            requested_location=dpf.locations.elemental,
        )
        for id, ref_value in ref_hv_values[ply_name].items():
            # print(f"Comparing elemental hv of id {id}")
            current = elemental_values.get_entity_data_by_id(id)
            # print(f"{id}: {ref_value} vs {current}")
            np.testing.assert_almost_equal(
                current[0],
                ref_value,
                err_msg=f"Elemental hv of id {id} does not match. Ply {ply_name}",
            )
