"""Helper to get example files."""

from dataclasses import asdict, dataclass
import os
import tempfile
from typing import Dict, Optional, Union, cast
import urllib.request

import ansys.dpf.core as dpf

from ansys.dpf.composites.load_plugin import load_composites_plugin

from .._typing_helper import PATH as _PATH

# Todo switch to official data repo once the PR is merged
EXAMPLE_REPO = (
    "https://github.com/janvonrickenbach/example-data/raw/"
    "feat/add_basic_pydpf_composites_examples/pydpf-composites/"
)


@dataclass(frozen=True)
class ServerContext:
    """Server context todo: Add context information."""

    server: dpf.server


@dataclass
class LongFiberCompositesFiles:
    """Container for long fiber file paths."""

    rst: _PATH = ""
    composite_definitions: _PATH = ""
    engineering_data: _PATH = ""


@dataclass
class ShortFiberCompositesFiles:
    """Container for short fiber file paths."""

    rst: Optional[_PATH] = ""
    dsdat: Optional[_PATH] = ""
    engineering_data: Optional[_PATH] = ""


@dataclass
class _LongFiberCompositesExampleFilenames:
    rst: str
    composite_definitions: str
    engineering_data: str


@dataclass
class _ShortfiberCompositesExampleFilenames:
    rst: str
    dsdat: str
    engineering_data: str


@dataclass
class _LongFiberExampleLocation:
    directory: str
    files: _LongFiberCompositesExampleFilenames


@dataclass
class _ShortFiberExampleLocation:
    directory: str
    files: _ShortfiberCompositesExampleFilenames


_long_fiber_examples: Dict[str, _LongFiberExampleLocation] = {
    "shell": _LongFiberExampleLocation(
        directory="shell",
        files=_LongFiberCompositesExampleFilenames(
            rst="shell.rst",
            engineering_data="material.engd",
            composite_definitions="ACPCompositeDefinitions.h5",
        ),
    )
}

_short_fiber_examples: Dict[str, _ShortFiberExampleLocation] = {
    "short_fiber": _ShortFiberExampleLocation(
        directory="short_fiber",
        files=_ShortfiberCompositesExampleFilenames(
            rst="file.rst", engineering_data="MatML.xml", dsdat="ds.dat"
        ),
    )
}


def connect_to_or_start_server() -> ServerContext:
    """Connect to or start a dpf server."""
    # Todo: add different modes to start or get the server
    server = dpf.server.connect_to_server("127.0.0.1", port=21002)
    load_composites_plugin()
    # Todo: return what type of server we have
    return ServerContext(server=server)


def _get_file_url(directory: str, filename: str) -> str:
    return EXAMPLE_REPO + "/".join([directory, filename])


def get_long_fiber_example_files(
    server_context: ServerContext, example_key: str
) -> LongFiberCompositesFiles:
    """Get long fiber example file by example key."""
    example_files = _long_fiber_examples[example_key]
    return cast(LongFiberCompositesFiles, _get_example_files(example_files, server_context.server))


def get_short_fiber_example_files(
    server_context: ServerContext, example_key: str
) -> ShortFiberCompositesFiles:
    """Get short fiber example file by example key."""
    example_files = _short_fiber_examples[example_key]
    return cast(ShortFiberCompositesFiles, _get_example_files(example_files, server_context.server))


def _get_example_files(
    example_files: Union[_ShortFiberExampleLocation, _LongFiberExampleLocation], server: dpf.server
) -> Union[ShortFiberCompositesFiles, LongFiberCompositesFiles]:
    composite_files_on_server: Union[ShortFiberCompositesFiles, LongFiberCompositesFiles]
    if isinstance(example_files, _ShortFiberExampleLocation):
        composite_files_on_server = ShortFiberCompositesFiles()
    else:
        composite_files_on_server = LongFiberCompositesFiles()
    with tempfile.TemporaryDirectory() as tmpdir:
        for key, filename in asdict(example_files.files).items():
            if filename is not None:
                file_url = _get_file_url(example_files.directory, filename)
                local_path = os.path.join(tmpdir, filename)
                urllib.request.urlretrieve(file_url, local_path)
                # if not server.local_server and not server.docker_config.use_docker:
                server_path = dpf.upload_file_in_tmp_folder(local_path, server=server)
                setattr(composite_files_on_server, key, server_path)

    return composite_files_on_server
