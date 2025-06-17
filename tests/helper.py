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

from dataclasses import dataclass
import os
import pathlib
import time
from typing import Any

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, Field, MeshedRegion, Operator
import numpy
import pytest

from ansys.dpf.composites._typing_helper import PATH as _PATH
from ansys.dpf.composites.data_sources import CompositeDefinitionFiles, get_composites_data_sources
from ansys.dpf.composites.example_helper import ContinuousFiberCompositesFiles
from ansys.dpf.composites.layup_info import add_layup_info_to_mesh
from ansys.dpf.composites.layup_info.material_operators import get_material_operators
from ansys.dpf.composites.server_helpers import upload_continuous_fiber_composite_files_to_server
from ansys.dpf.composites.unit_system import get_unit_system


class Timer:
    def __init__(self):
        self.timings = [("start", time.time())]

    def add(self, label):
        self.timings.append((label, time.time()))

    def summary(self):
        diffs = self._get_diffs()
        print("")
        print("Timer summary")
        for diff in diffs:
            print(diff)
        print(f"Total:{self._get_sum()}")
        print("")

    def get_runtime_without_first_step(self):
        """
        Gets the total runtime without the first entry. Useful
        if the first step does some setup that is not relevant for performance
        """
        return self._get_sum() - self._get_diffs()[0][1]

    def _get_sum(self):
        return sum([diff[1] for diff in self._get_diffs()])

    def _get_diffs(self):
        diffs = []
        for idx, timing in enumerate(self.timings):
            if idx > 0:
                diffs.append((timing[0], timing[1] - self.timings[idx - 1][1]))
        return diffs


@dataclass
class SetupResult:
    field: Field
    mesh: MeshedRegion
    rst_data_source: DataSources
    material_provider: Operator
    streams_provider: Operator
    layup_provider: Operator


def setup_operators(server, files: ContinuousFiberCompositesFiles):
    timer = Timer()

    files = upload_continuous_fiber_composite_files_to_server(data_files=files, server=server)

    data_sources = get_composites_data_sources(files)

    streams_provider = dpf.operators.metadata.streams_provider()
    streams_provider.inputs.data_sources.connect(data_sources.result_files)

    strain_operator = dpf.operators.result.elastic_strain()
    strain_operator.inputs.streams_container(streams_provider)
    strain_operator.inputs.bool_rotate_to_global(False)
    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)

    timer.add("stresses")

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.streams_container(streams_provider)
    mesh = mesh_provider.outputs.mesh()
    timer.add("mesh")

    unit_system = get_unit_system(data_sources.result_files)
    material_operators = get_material_operators(
        data_sources.result_files, data_sources.engineering_data, unit_system=unit_system
    )
    layup_provider = add_layup_info_to_mesh(
        data_sources=data_sources,
        mesh=mesh,
        material_operators=material_operators,
        unit_system=unit_system,
    )

    return SetupResult(
        field=fields_container[0],
        mesh=mesh,
        rst_data_source=data_sources.result_files,
        material_provider=material_operators.material_provider,
        streams_provider=streams_provider,
        layup_provider=layup_provider,
    )


def get_basic_shell_files(two_load_steps: bool = False):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    if two_load_steps:
        rst_path = TEST_DATA_ROOT_DIR / "shell_2load_steps.rst"
    else:
        rst_path = TEST_DATA_ROOT_DIR / "shell.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return ContinuousFiberCompositesFiles(
        result_files=[rst_path],
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )


def get_dummy_data_files(distributed: bool = False):
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    if distributed:
        rst_path: _PATH | list[_PATH] = [
            os.path.join(TEST_DATA_ROOT_DIR, f"distributed_shell{i}.rst") for i in range(2)
        ]
    else:
        rst_path = os.path.join(TEST_DATA_ROOT_DIR, "shell.rst")
    h5_path = os.path.join(TEST_DATA_ROOT_DIR, "ACPCompositeDefinitions.h5")
    material_path = os.path.join(TEST_DATA_ROOT_DIR, "material.engd")
    return ContinuousFiberCompositesFiles(
        result_files=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )


def compare_sampling_point_results(
    sample: dict[Any, Any], reference: dict[Any, Any], with_polar_properties: bool
) -> None:
    assert (
        sample["element_label"] == reference["element_label"]
    ), f"Label {sample['element_label']} != {reference['element_label']}"
    assert (
        sample["unit_system"] == reference["unit_system"]
    ), f"Unit system {sample['unit_system']} != {reference['unit_system']}"

    assert sample["layup"]["num_analysis_plies"] == reference["layup"]["num_analysis_plies"], (
        f"Analysis Plies {sample['layup']['num_analysis_plies']} !="
        " {reference['layup']['num_analysis_plies']}"
    )
    assert (
        sample["layup"]["offset"] == reference["layup"]["offset"]
    ), f"Offset {sample['layup']['offset']} != {reference['layup']['offset']}"
    if not with_polar_properties:
        assert sample["layup"]["polar_properties"] is None
    else:
        raise RuntimeError("Float comparison of polar properties is not implemented.")

    assert len(sample["layup"]["analysis_plies"]) == len(
        reference["layup"]["analysis_plies"]
    ), f"{len(sample['layup']['analysis_plies'])} != {len(reference['layup']['analysis_plies'])}"
    for ap_index, ap in enumerate(sample["layup"]["analysis_plies"]):
        ref_ap = reference["layup"]["analysis_plies"][ap_index]
        assert ap.keys() == ref_ap.keys()
        for key in ap.keys():
            if key in ["angle", "thickness"]:
                assert ap[key] == pytest.approx(
                    ref_ap[key], abs=1e-8, rel=1e-6
                ), f"{key} mismatch. {ap} != {ref_ap}"
            else:
                assert ap[key] == ref_ap[key], f"{key} mismatch. {ap} != {ref_ap}"

    result_keys = ["failures", "strains", "stresses", "offsets"]
    reference_results = reference["results"]
    sample_results = sample["results"]
    for key in result_keys:
        if key == "offsets":
            numpy.testing.assert_allclose(
                sample_results[key],
                reference_results[key],
                rtol=1e-6,
                atol=1e-8,
                err_msg=f"Values '{key}' mismatch.",
            )
        else:
            assert sample_results[key].keys() == reference_results[key].keys(), (
                f"Keys mismatch for {key}. Expected {reference_results[key].keys()}"
                f" but got {sample_results[key].keys()}."
            )
            for component in sample_results[key].keys():
                if component == "failure_modes":
                    # compare list of strings
                    assert sample_results[key][component] == reference_results[key][component], (
                        f"{key}/{component} mismatch: {sample_results[key][component]} "
                        f"!= {reference_results[key][component]}"
                    )
                else:
                    numpy.testing.assert_allclose(
                        sample_results[key][component],
                        reference_results[key][component],
                        rtol=1e-6,
                        atol=1e-8,
                        err_msg=f"Values '{key} - {component}' mismatch.",
                    )
