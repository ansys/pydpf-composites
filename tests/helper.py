from dataclasses import dataclass
import pathlib
import time

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, Field, MeshedRegion, Operator

from ansys.dpf.composites.data_sources import CompositeDefinitionFiles, get_composites_data_sources
from ansys.dpf.composites.example_helper import (
    ContinuousFiberCompositesFiles,
    upload_continuous_fiber_composite_files_to_server,
)
from ansys.dpf.composites.layup_info import add_layup_info_to_mesh
from ansys.dpf.composites.layup_info.material_operators import get_material_operators


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

    if not server.local_server:
        files = upload_continuous_fiber_composite_files_to_server(data_files=files, server=server)

    data_sources = get_composites_data_sources(files)

    streams_provider = dpf.operators.metadata.streams_provider()
    streams_provider.inputs.data_sources.connect(data_sources.rst)

    strain_operator = dpf.operators.result.elastic_strain()
    strain_operator.inputs.streams_container(streams_provider)
    strain_operator.inputs.bool_rotate_to_global(False)
    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)

    timer.add("stresses")

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.streams_container(streams_provider)
    mesh = mesh_provider.outputs.mesh()
    timer.add("mesh")

    material_operators = get_material_operators(data_sources.rst, data_sources.engineering_data)
    layup_provider = add_layup_info_to_mesh(
        data_sources=data_sources, mesh=mesh, material_operators=material_operators
    )

    return SetupResult(
        field=fields_container[0],
        mesh=mesh,
        rst_data_source=data_sources.rst,
        material_provider=material_operators.material_provider,
        streams_provider=streams_provider,
        layup_provider=layup_provider,
    )


def get_basic_shell_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = TEST_DATA_ROOT_DIR / "shell.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return ContinuousFiberCompositesFiles(
        rst=rst_path,
        composite={"shell": CompositeDefinitionFiles(definition=h5_path)},
        engineering_data=material_path,
    )
