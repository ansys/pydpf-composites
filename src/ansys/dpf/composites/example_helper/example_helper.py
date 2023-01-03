"""Helper to get example files."""

from dataclasses import dataclass, field
import os
import tempfile
from typing import Collection, Dict, Sequence, cast
import urllib.request

import ansys.dpf.core as dpf

from .._typing_helper import PATH as _PATH
from ..composite_data_sources import (
    CompositeFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
)
from ..load_plugin import load_composites_plugin

EXAMPLE_REPO = "https://github.com/pyansys/example-data/raw/master/pydpf-composites/"


@dataclass(frozen=True)
class ServerContext:
    """Server context todo: Add context information."""

    server: dpf.server


def upload_short_fiber_composite_files_to_server(
    data_files: ShortFiberCompositesFiles, server: dpf.server
) -> ShortFiberCompositesFiles:
    """Upload short fiber composites files to server.

    Parameters
    ----------
    data_files
    server
    """

    def upload(filename: _PATH) -> str:
        return cast(str, dpf.upload_file_in_tmp_folder(filename, server=server))

    return ShortFiberCompositesFiles(
        rst=upload(data_files.engineering_data),
        dsdat=upload(data_files.dsdat),
        engineering_data=upload(data_files.engineering_data),
    )


def upload_continuous_fiber_composite_files_to_server(
    data_files: ContinuousFiberCompositesFiles, server: dpf.server
) -> ContinuousFiberCompositesFiles:
    """Upload short fiber composites files to server.

    Parameters
    ----------
    data_files
    server
    """

    def upload(filename: _PATH) -> str:
        return cast(str, dpf.upload_file_in_tmp_folder(filename, server=server))

    all_composite_files = []
    for composite_files_by_scope in data_files.composite_files:
        mapping_files = [
            upload(mapping_file) for mapping_file in composite_files_by_scope.mapping_files
        ]
        all_composite_files.append(
            CompositeFiles(
                composite_definitions=upload(composite_files_by_scope.composite_definitions),
                mapping_files=mapping_files,
            )
        )

    return ContinuousFiberCompositesFiles(
        rst=upload(data_files.rst),
        engineering_data=upload(data_files.engineering_data),
        composite_files=all_composite_files,
    )


@dataclass
class _ContinuousFiberCompositeFiles:
    composite_definitions: str
    mapping_files: Collection[str] = field(default_factory=lambda: [])


@dataclass
class _ContinuousFiberCompositesExampleFilenames:
    rst: str
    composite_files: Sequence[_ContinuousFiberCompositeFiles]
    engineering_data: str


@dataclass
class _ShortFiberCompositesExampleFilenames:
    rst: str
    dsdat: str
    engineering_data: str


@dataclass
class _ContinuousFiberExampleLocation:
    """Location of the a given continuous fiber example in the example_data repo.

    Parameters
    ----------
    directory
        Directory in example_data/pydpf-composites
    files
        Example files in directory
    """

    directory: str
    files: _ContinuousFiberCompositesExampleFilenames


@dataclass
class _ShortFiberExampleLocation:
    """Location of the a given short fiber example in the example_data repo.

    Parameters
    ----------
    directory
        Directory in example_data/pydpf-composites
    files
        Example files in directory
    """

    directory: str
    files: _ShortFiberCompositesExampleFilenames


_continuous_fiber_examples: Dict[str, _ContinuousFiberExampleLocation] = {
    "shell": _ContinuousFiberExampleLocation(
        directory="shell",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="shell.rst",
            engineering_data="material.engd",
            composite_files=[
                _ContinuousFiberCompositeFiles(
                    composite_definitions="ACPCompositeDefinitions.h5",
                )
            ],
        ),
    ),
    "ins": _ContinuousFiberExampleLocation(
        directory="ins",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="beam_181_analysis_model.rst",
            engineering_data="materials.xml",
            composite_files=[
                _ContinuousFiberCompositeFiles(
                    composite_definitions="ACPCompositeDefinitions.h5",
                )
            ],
        ),
    ),
    "assembly_shell": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="file.rst",
            engineering_data="material.engd",
            composite_files=[
                _ContinuousFiberCompositeFiles(
                    composite_definitions="ACPCompositeDefinitions.h5",
                    mapping_files=["ACPCompositeDefinitions.mapping"],
                )
            ],
        ),
    ),
    "assembly_solid": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="file.rst",
            engineering_data="material.engd",
            composite_files=[
                _ContinuousFiberCompositeFiles(
                    composite_definitions="ACPSolidModel_SM.h5",
                    mapping_files=["ACPSolidModel_SM.mapping"],
                )
            ],
        ),
    ),
}

_short_fiber_examples: Dict[str, _ShortFiberExampleLocation] = {
    "short_fiber": _ShortFiberExampleLocation(
        directory="short_fiber",
        files=_ShortFiberCompositesExampleFilenames(
            rst="file.rst", engineering_data="MatML.xml", dsdat="ds.dat"
        ),
    )
}


def connect_to_or_start_server() -> ServerContext:
    """Connect to or start a dpf server."""
    # Todo: add different modes to start or get the server
    # Currently just connects to a hardcoded port

    server = dpf.server.connect_to_server("127.0.0.1", port=21002)
    load_composites_plugin(server)
    return ServerContext(server=server)


def _get_file_url(directory: str, filename: str) -> str:
    return EXAMPLE_REPO + "/".join([directory, filename])


def _download_and_upload_file(
    directory: str, filename: str, tmpdir: str, server: dpf.server
) -> str:
    """Download example file from example_data repo and and upload it the the dpf server."""
    file_url = _get_file_url(directory, filename)
    local_path = os.path.join(tmpdir, filename)
    urllib.request.urlretrieve(file_url, local_path)
    # todo: With 0.7.1 the server will have
    #  a boolean property 'local_server' that we can use to
    #  determine if files should be uploaded
    return cast(str, dpf.upload_file_in_tmp_folder(local_path, server=server))


def get_short_fiber_example_files(
    example_key: str,
    server_context: ServerContext,
) -> ShortFiberCompositesFiles:
    """Get short fiber example file by example key."""
    example_files = _short_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def upload(filename: str) -> str:
            return _download_and_upload_file(
                example_files.directory, filename, tmpdir, server_context.server
            )

    return ShortFiberCompositesFiles(
        rst=upload(example_files.files.rst),
        dsdat=upload(example_files.files.dsdat),
        engineering_data=upload(example_files.files.engineering_data),
    )


def get_continuous_fiber_example_files(
    example_key: str,
    server_context: ServerContext,
) -> ContinuousFiberCompositesFiles:
    """Get continuous fiber example file by example key."""
    example_files = _continuous_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def upload(filename: str) -> str:
            return _download_and_upload_file(
                example_files.directory, filename, tmpdir, server_context.server
            )

        all_composite_files = []
        for composite_examples_files_for_scope in example_files.files.composite_files:
            mapping_file_paths = [
                upload(mapping_file)
                for mapping_file in composite_examples_files_for_scope.mapping_files
            ]
            composite_files = CompositeFiles(
                composite_definitions=upload(
                    composite_examples_files_for_scope.composite_definitions
                ),
                mapping_files=mapping_file_paths,
            )
            all_composite_files.append(composite_files)

        return ContinuousFiberCompositesFiles(
            rst=upload(example_files.files.rst),
            engineering_data=upload(example_files.files.engineering_data),
            composite_files=all_composite_files,
        )
