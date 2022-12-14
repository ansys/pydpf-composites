"""Helper to get example files."""

from dataclasses import asdict, dataclass
import os
import tempfile
from typing import Dict, Optional, TypeVar, Union, cast
import urllib.request

import ansys.dpf.core as dpf

from ansys.dpf.composites.load_plugin import load_composites_plugin

from .._typing_helper import PATH as _PATH

EXAMPLE_REPO = "https://github.com/pyansys/example-data/raw/master/pydpf-composites/"


@dataclass(frozen=True)
class ServerContext:
    """Server context todo: Add context information."""

    server: dpf.server


@dataclass
class ContinuousFiberCompositesFiles:
    """Container for continuous fiber file paths."""

    rst: _PATH = ""
    composite_definitions: _PATH = ""
    engineering_data: _PATH = ""


@dataclass
class ShortFiberCompositesFiles:
    """Container for short fiber file paths."""

    rst: Optional[_PATH] = ""
    dsdat: Optional[_PATH] = ""
    engineering_data: Optional[_PATH] = ""


FilesType = TypeVar("FilesType", ShortFiberCompositesFiles, ContinuousFiberCompositesFiles)


def upload_composite_files_to_server(data_files: FilesType, server: dpf.server) -> FilesType:
    """Upload composites files to server.

    Parameters
    ----------
    data_files
    server
    """
    if isinstance(data_files, ShortFiberCompositesFiles):
        server_files: FilesType = ShortFiberCompositesFiles()
    else:
        server_files = ContinuousFiberCompositesFiles()
    for key, filename in asdict(data_files).items():
        server_file = dpf.upload_file_in_tmp_folder(filename, server=server)
        setattr(server_files, key, server_file)
    return server_files


@dataclass
class _ContinuousFiberCompositesExampleFilenames:
    rst: str
    composite_definitions: str
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
            composite_definitions="ACPCompositeDefinitions.h5",
        ),
    ),
    "ins": _ContinuousFiberExampleLocation(
        directory="ins",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="beam_181_analysis_model.rst",
            engineering_data="materials.xml",
            composite_definitions="ACPCompositeDefinitions.h5",
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


def get_continuous_fiber_example_files(
    server_context: ServerContext, example_key: str
) -> ContinuousFiberCompositesFiles:
    """Get continuous fiber example file by example key."""
    example_files = _continuous_fiber_examples[example_key]
    return cast(ContinuousFiberCompositesFiles, _get_example_files(example_files, server_context))


def get_short_fiber_example_files(
    server_context: ServerContext, example_key: str
) -> ShortFiberCompositesFiles:
    """Get short fiber example file by example key."""
    example_files = _short_fiber_examples[example_key]
    return cast(ShortFiberCompositesFiles, _get_example_files(example_files, server_context))


def _get_example_files(
    example_files: Union[_ShortFiberExampleLocation, _ContinuousFiberExampleLocation],
    server_context: ServerContext,
) -> Union[ShortFiberCompositesFiles, ContinuousFiberCompositesFiles]:
    composite_files_on_server: Union[ShortFiberCompositesFiles, ContinuousFiberCompositesFiles]
    if isinstance(example_files, _ShortFiberExampleLocation):
        composite_files_on_server = ShortFiberCompositesFiles()
    else:
        composite_files_on_server = ContinuousFiberCompositesFiles()
    with tempfile.TemporaryDirectory() as tmpdir:
        for key, filename in asdict(example_files.files).items():
            if filename is not None:
                file_url = _get_file_url(example_files.directory, filename)
                local_path = os.path.join(tmpdir, filename)
                urllib.request.urlretrieve(file_url, local_path)
                # todo: With 0.7.1 the server will have
                #  a boolean property 'local_server' that we can use to
                # determine if files should be uploaded
                server_path = dpf.upload_file_in_tmp_folder(
                    local_path, server=server_context.server
                )
                setattr(composite_files_on_server, key, server_path)

    return composite_files_on_server
