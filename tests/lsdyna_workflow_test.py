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
from ansys.dpf.composites.constants import SolverType, Sym3x3TensorComponent
from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
from ansys.dpf.composites.layup_info import get_all_analysis_ply_names
from ansys.dpf.composites.ply_wise_data import SpotReductionStrategy, get_ply_wise_data
from ansys.dpf.composites.server_helpers import version_older_than


def test_composite_model_with_rst_only(dpf_server):

    if version_older_than(dpf_server, "10.0"):
        pytest.xfail("Post-processing of LSDyna solutions requires DPF server 10.0 or later.")

    test_data_dir = pathlib.Path(__file__).parent / "data" / "lsdyna" / "basic_shell_model"

    composite_files = get_composite_files_from_workbench_result_folder(
        result_folder=test_data_dir,
        ensure_composite_definitions_found=True,
        solver_type=SolverType.LSDYNA,
    )

    assert str(composite_files.solver_input_file).endswith("input.k")
    assert len(composite_files.rst) == 1
    assert str(composite_files.rst[0]).endswith("d3plot")
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
    assert all_ply_names == [
        "P1L1__ModelingPly.1",
        "P1L1__ModelingPly.9",
        "P1L1__ModelingPly.8",
        "P1L1__ModelingPly.7",
        "P1L1__ModelingPly.6",
        "P1L1__ModelingPly.5",
    ]

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
    keyword_options_as_json = json.loads(keyword_parser.outputs[0].get_data())

    maxint = int(keyword_options_as_json["maxint"])
    assert maxint == 6

    stress_container = stress_operator.get_output(pin=0, output_type=dpf.types.fields_container)
    strip_operator = Operator("composite::ls_dyna_preparing_results")
    strip_operator.inputs.maxint(maxint)
    strip_operator.inputs.fields_container(stress_container)
    strip_operator.inputs.mesh(composite_model.get_mesh())

    stripped_stress_field = strip_operator.get_output(
        pin=0, output_type=dpf.types.fields_container
    )[0]

    ref_stresses = {
        "P1L1__ModelingPly.1": [
            0.78046584,
            0.48736653,
            0.62010139,
            0.76608545,
            0.5902319,
            0.61697829,
            0.63654315,
            0.63733745,
            0.48250192,
            1.01434195,
            0.42740965,
            0.70846915,
            0.78566492,
            0.56781751,
            0.75876641,
            1.07498252,
            0.39696938,
            1.12905777,
            0.69972301,
            0.88228053,
            0.61887008,
            0.84789705,
            0.79138935,
            0.70147991,
            0.88183904,
            0.40101856,
            0.76288044,
            0.38967335,
            0.58237743,
            0.5506863,
            0.59274179,
            0.74999774,
            0.60418034,
            1.07735205,
            0.38777238,
            0.54397643,
            0.6294992,
        ],
        "P1L1__ModelingPly.8": [
            2.35633779,
            1.68521047,
            1.98230875,
            1.6439842,
            1.27931714,
            1.7312119,
            2.15088344,
            2.072716,
            1.61682951,
            3.61598635,
            3.74071383,
            1.43789935,
            3.8962903,
            1.97693849,
            2.48541856,
            1.47184443,
            4.00257063,
            4.369771,
            1.22651052,
            1.03484726,
            0.8601858,
            3.35434079,
            1.877491,
            1.86350453,
            1.78633785,
            1.80465424,
            1.3003,
            1.49408126,
            1.59000432,
            2.76951575,
            2.58470726,
            2.30126381,
            1.87349033,
            2.18899775,
            2.50676799,
            2.31054258,
            1.99764073,
            1.57307851,
            1.38659024,
            1.59543991,
            5.4631424,
            4.58185339,
            1.29251909,
            1.87710023,
            6.00918484,
            4.19732428,
            3.17169046,
            2.29245949,
            1.22937775,
            1.44112408,
            0.97444618,
            1.86350417,
            1.80961812,
            4.06457138,
            3.36544013,
            1.61584389,
            3.76847076,
            1.12461841,
            1.88982403,
            0.76165456,
            1.91653562,
            2.20422125,
            1.58440042,
            4.1215024,
            3.75976038,
            1.06810224,
            1.263188,
            0.77870363,
            1.1416471,
            1.91748786,
            1.92303967,
            1.27208698,
            1.50735271,
            1.44010699,
            3.87609029,
            1.25596857,
            1.09891677,
            1.22522676,
            1.24634123,
            1.13394094,
            2.36943007,
            1.88601828,
            2.12744999,
            2.35881281,
            2.1890521,
            0.85002595,
            2.33557177,
            1.47503805,
            1.03108621,
            0.87819612,
            1.7426182,
            1.70565844,
            2.52401447,
            2.80813789,
            1.40416157,
            1.45422685,
            1.47231662,
            1.35573816,
            0.73687553,
            5.28532887,
            4.28070354,
            1.27458441,
            2.05423546,
            5.38226604,
            3.77182746,
            3.06230474,
            2.31908488,
            1.2896564,
            1.30260313,
            1.06426847,
            1.21887481,
            1.23222315,
            1.09410155,
            2.2888782,
            2.32547188,
            1.90818143,
            2.07520366,
            2.13933134,
            1.84982252,
            1.76198006,
            1.47503865,
            0.59762663,
            0.52338862,
            0.52419442,
            0.6923148,
            0.64600569,
            0.53147852,
            0.53412086,
            0.56753165,
            0.49967134,
            0.80070162,
            0.53078914,
            0.5564208,
            0.67498606,
            0.6197499,
            0.73893654,
            0.97299284,
            0.54734725,
            0.81503296,
            0.5951668,
            0.63393694,
            0.73662704,
            0.70224524,
            0.59040475,
            0.54220366,
            0.6385389,
            0.53166825,
            0.67660826,
            0.60615891,
            0.56330681,
            0.65881276,
            0.6386475,
            0.82728702,
            0.60904145,
            0.91787791,
            0.55212384,
            0.58747822,
            0.51493227,
        ],
    }

    for ply_name, ref_values in ref_stresses.items():
        print(f"Comparing stresses of {ply_name}")

        elemental_values = get_ply_wise_data(
            field=stripped_stress_field,
            ply_name=ply_name,
            mesh=composite_model.get_mesh(),
            component=Sym3x3TensorComponent.TENSOR11,
            spot_reduction_strategy=SpotReductionStrategy.AVG,
            requested_location=dpf.locations.elemental,
        )
        np.testing.assert_allclose(elemental_values.data, ref_values)

    # verify that data extraction also works for history variables
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

    stripped_hv_field = stripped_hv_container.get_field({"time": time_ids[-1], "ihv": 12})

    ref_hv_values = {
        "P1L1__ModelingPly.1": [
            1.97112986e-05,
            -3.93044866e-05,
            1.19656788e-05,
            6.07134825e-05,
            2.58394102e-05,
            1.07657788e-05,
            7.95276173e-06,
            1.65774436e-05,
            1.16018873e-05,
            -3.19624924e-05,
            -9.79147990e-06,
            -1.59082738e-05,
            1.19799643e-05,
            3.54364201e-05,
            1.40151451e-05,
            -3.96173236e-05,
            -3.00575794e-05,
            9.88709435e-05,
            -3.46116110e-07,
            3.60020704e-06,
            -1.16412411e-04,
            -1.02680278e-05,
            1.96129918e-06,
            -2.28648350e-05,
            -1.90280434e-06,
            -4.10303473e-05,
            3.31152514e-05,
            -5.04648688e-06,
            -3.03604502e-05,
            -4.21166951e-05,
            1.36143299e-05,
            -2.57038446e-05,
            3.76737844e-05,
            -3.98508491e-05,
            -2.13678268e-05,
            -1.25913891e-06,
            1.60224135e-05,
        ],
        "P1L1__ModelingPly.8": [
            1.05320371e-03,
            7.12289824e-04,
            8.18834582e-04,
            6.46863191e-04,
            4.58102324e-04,
            6.94356684e-04,
            8.74494843e-04,
            8.99484963e-04,
            6.25203189e-04,
            1.55081926e-03,
            1.34654716e-03,
            5.73547441e-04,
            1.47108175e-03,
            8.16900807e-04,
            1.02941343e-03,
            5.72868448e-04,
            1.71233329e-03,
            1.59463240e-03,
            4.70985251e-04,
            3.83696693e-04,
            9.20657767e-04,
            3.60372269e-06,
            5.81652857e-04,
            3.37428239e-04,
            7.66098441e-04,
            7.72686326e-04,
            4.61617572e-04,
            6.47651730e-04,
            6.61607366e-04,
            1.16153876e-03,
            1.21631112e-03,
            1.06090680e-03,
            8.60035187e-04,
            9.84887127e-04,
            1.01829309e-03,
            9.70880326e-04,
            8.24333634e-04,
            7.08735315e-04,
            5.85639325e-04,
            6.79277873e-04,
            2.46897875e-03,
            1.73241843e-03,
            1.33601518e-03,
            9.33033472e-04,
            2.28469819e-03,
            1.79429085e-03,
            9.33874166e-04,
            8.31690384e-04,
            5.35256928e-04,
            5.68195246e-04,
            4.17204399e-04,
            3.37428384e-04,
            6.52275165e-04,
            1.47148874e-03,
            -1.08252025e-05,
            7.06769468e-04,
            1.60970236e-03,
            4.71665000e-04,
            8.36272549e-04,
            3.04405723e-04,
            8.45012255e-04,
            1.03400368e-03,
            7.17550574e-04,
            1.50811672e-03,
            1.56016706e-03,
            4.72216401e-04,
            5.07824705e-04,
            3.02100496e-04,
            4.24880738e-04,
            8.15719774e-04,
            8.83288449e-04,
            5.52698970e-04,
            6.23615924e-04,
            6.27347617e-04,
            1.51650282e-03,
            5.00158174e-04,
            4.20701777e-04,
            5.14819927e-04,
            5.54009690e-04,
            4.73314198e-04,
            1.00007921e-03,
            8.10990110e-04,
            8.93249176e-04,
            9.91710578e-04,
            9.35701304e-04,
            9.18651116e-04,
            4.99590882e-04,
            4.17163857e-04,
            4.35234164e-04,
            4.23351041e-04,
            7.55050336e-04,
            7.37183727e-04,
            1.21465581e-03,
            1.11428974e-03,
            6.01086300e-04,
            6.59956480e-04,
            6.42514147e-04,
            5.91984135e-04,
            3.12986405e-04,
            2.36732676e-03,
            1.60789024e-03,
            1.32913783e-03,
            8.80426262e-04,
            2.30002869e-03,
            1.64921815e-03,
            9.27567133e-04,
            8.47436255e-04,
            5.49731310e-04,
            5.56369196e-04,
            4.67961625e-04,
            5.54699916e-04,
            5.38185239e-04,
            4.78794798e-04,
            9.19109792e-04,
            9.16761986e-04,
            7.91934028e-04,
            1.04288734e-03,
            9.96260438e-04,
            8.47697200e-04,
            6.88898086e-04,
            4.17163857e-04,
            2.08736805e-04,
            1.61621807e-04,
            1.74389832e-04,
            2.70853518e-04,
            2.14710584e-04,
            1.72108994e-04,
            1.77261274e-04,
            2.01616742e-04,
            1.66651240e-04,
            2.60820467e-04,
            1.89121929e-04,
            1.78180126e-04,
            2.47964053e-04,
            2.27062730e-04,
            2.53707491e-04,
            3.31458024e-04,
            1.92144827e-04,
            3.73952789e-04,
            2.20595626e-04,
            2.37815577e-04,
            2.52234895e-04,
            2.61396257e-04,
            2.19546040e-04,
            1.92266205e-04,
            2.32221442e-04,
            1.90609207e-04,
            2.68154283e-04,
            2.39440167e-04,
            2.04065014e-04,
            2.50167417e-04,
            2.45778239e-04,
            3.00307089e-04,
            2.52142898e-04,
            3.52827803e-04,
            1.94613443e-04,
            2.12871557e-04,
            1.91635321e-04,
        ],
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
        np.testing.assert_allclose(elemental_values.data, ref_values)
