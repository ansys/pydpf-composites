from contextlib import contextmanager
from dataclasses import dataclass
import pathlib
import time
from typing import Generator

import ansys.dpf.core as dpf
from ansys.dpf.core import DataSources, Field, MeshedRegion, Operator

from ansys.dpf.composites.example_helper.example_helper import LongFiberCompositesFiles
from ansys.dpf.composites.layup_info import ElementInfoProvider, get_element_info_provider


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


def setup_operators(server, files: LongFiberCompositesFiles, upload=True):

    timer = Timer()
    eng_data_path = files.engineering_data
    h5_path = files.composite_definitions
    rst_path = files.rst

    if upload:
        rst_path = dpf.upload_file_in_tmp_folder(files.rst, server=server)

        h5_path = dpf.upload_file_in_tmp_folder(files.composite_definitions, server=server)
        eng_data_path = dpf.upload_file_in_tmp_folder(files.engineering_data, server=server)

    eng_data_source = dpf.DataSources()
    eng_data_source.add_file_path(eng_data_path, "EngineeringData")

    composite_definitions_source = dpf.DataSources()
    composite_definitions_source.add_file_path(h5_path, "CompositeDefinitions")

    rst_data_source = dpf.DataSources(rst_path)
    streams_provider = dpf.operators.metadata.streams_provider()
    streams_provider.inputs.data_sources.connect(rst_data_source)

    strain_operator = dpf.Operator("EPEL")
    strain_operator.inputs.streams_container(streams_provider)
    strain_operator.inputs.bool_rotate_to_global(False)

    fields_container = strain_operator.get_output(output_type=dpf.types.fields_container)

    timer.add("stresses")

    mesh_provider = dpf.Operator("MeshProvider")
    mesh_provider.inputs.streams_container(streams_provider)
    mesh = mesh_provider.outputs.mesh()
    timer.add("mesh")

    material_support_provider = dpf.Operator("support_provider")
    material_support_provider.inputs.property("mat")
    material_support_provider.inputs.streams_container(streams_provider)

    result_info_provider = dpf.Operator("ResultInfoProvider")
    result_info_provider.inputs.streams_container(streams_provider)

    material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
    material_provider.inputs.data_sources = eng_data_source
    material_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    material_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    material_provider.inputs.Engineering_data_file(eng_data_source)

    layup_provider = dpf.Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh_provider.outputs.mesh)
    layup_provider.inputs.data_sources(composite_definitions_source)
    layup_provider.inputs.abstract_field_support(
        material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(result_info_provider.outputs.result_info)
    layup_provider.run()

    timer.add("layup")

    # timer.summary()

    return SetupResult(
        field=fields_container[0],
        mesh=mesh,
        rst_data_source=rst_data_source,
        material_provider=material_provider,
        streams_provider=streams_provider,
        layup_provider=layup_provider,
    )


@dataclass(frozen=True)
class FieldInfo:
    field: Field
    layup_info: ElementInfoProvider


@contextmanager
def get_field_info(
    input_field: Field, mesh: MeshedRegion, data_source: DataSources
) -> Generator[FieldInfo, None, None]:
    layup_info = get_element_info_provider(mesh, stream_provider_or_data_source=data_source)
    with input_field.as_local_field() as local_input_field:
        yield FieldInfo(field=local_input_field, layup_info=layup_info)


def get_basic_shell_files():
    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell"

    rst_path = TEST_DATA_ROOT_DIR / "shell.rst"
    h5_path = TEST_DATA_ROOT_DIR / "ACPCompositeDefinitions.h5"
    material_path = TEST_DATA_ROOT_DIR / "material.engd"
    return LongFiberCompositesFiles(
        rst=rst_path, composite_definitions=h5_path, engineering_data=material_path
    )
