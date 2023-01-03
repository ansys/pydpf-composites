"""Helper to get example files."""

from dataclasses import asdict, dataclass, field
import os
import tempfile
from typing import Collection, Dict, List, TypeVar, Union, cast
import urllib.request

import ansys.dpf.core as dpf

from ..composite_data_sources import ContinuousFiberCompositesFiles, ShortFiberCompositesFiles
from ..load_plugin import load_composites_plugin

EXAMPLE_REPO = "https://github.com/pyansys/example-data/raw/master/pydpf-composites/"


@dataclass(frozen=True)
class ServerContext:
    """Server context todo: Add context information."""

    server: dpf.server


FilesType = TypeVar("FilesType", ShortFiberCompositesFiles, ContinuousFiberCompositesFiles)


def upload_composite_files_to_server(data_files: FilesType, server: dpf.server) -> FilesType:
    """Upload composites files to server.

    Parameters
    ----------
    data_files
    server
    """
    filedict: Dict[str, Union[str, List[str]]] = {}

    for key, filename_or_filenames in asdict(data_files).items():
        if key == "mapping_files":
            filenames = filename_or_filenames
            filedict[key] = []
            for filename in filenames:
                server_file = dpf.upload_file_in_tmp_folder(filename, server=server)
                filedict[key].append(server_file)  # type: ignore
        else:
            server_file = dpf.upload_file_in_tmp_folder(filename_or_filenames, server=server)
            filedict[key] = server_file

    if isinstance(data_files, ShortFiberCompositesFiles):
        return ShortFiberCompositesFiles(**filedict)  # type:ignore
    else:
        return ContinuousFiberCompositesFiles(**filedict)  # type:ignore


@dataclass
class _ContinuousFiberCompositesExampleFilenames:
    rst: str
    composite_definitions: str
    engineering_data: str
    mapping_files: Collection[str] = field(default_factory=lambda: [])


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
    "assembly_shell": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="file.rst",
            engineering_data="material.engd",
            composite_definitions="ACPCompositeDefinitions.h5",
            mapping_files=["ACPCompositeDefinitions.mapping"],
        ),
    ),
    "assembly_solid": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="file.rst",
            engineering_data="material.engd",
            composite_definitions="ACPSolidModel_SM.h5",
            mapping_files=["ACPSolidModel_SM.mapping"],
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


def _get_example_files(
    example_files: Union[_ShortFiberExampleLocation, _ContinuousFiberExampleLocation],
    server_context: ServerContext,
) -> Union[ShortFiberCompositesFiles, ContinuousFiberCompositesFiles]:
    composite_files_on_server: Union[ShortFiberCompositesFiles, ContinuousFiberCompositesFiles]

    files_dict: Dict[str, Union[str, List[str]]] = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        for key, filename_or_filenames in asdict(example_files.files).items():
            if filename_or_filenames is not None:
                if key == "mapping_files":
                    files_dict[key] = []
                    for filename in filename_or_filenames:
                        files_dict[key].append(  # type: ignore
                            _download_and_upload_file(
                                example_files.directory, filename, tmpdir, server_context.server
                            )
                        )
                else:
                    files_dict[key] = _download_and_upload_file(
                        example_files.directory,
                        filename_or_filenames,
                        tmpdir,
                        server_context.server,
                    )

    if isinstance(example_files, _ShortFiberExampleLocation):
        return ShortFiberCompositesFiles(**files_dict)  # type:ignore
    else:
        return ContinuousFiberCompositesFiles(**files_dict)  # type:ignore
