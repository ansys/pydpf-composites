"""Helper to get example files."""

from dataclasses import dataclass
import os
import tempfile
from typing import Any, Callable, Dict, Optional, cast
import urllib.request

import ansys.dpf.core as dpf

from .._typing_helper import PATH as _PATH
from ..composite_data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
)
from ..load_plugin import load_composites_plugin

EXAMPLE_REPO = "https://github.com/pyansys/example-data/raw/master/pydpf-composites/"


def _try_until_timeout(fun: Callable[[], Any], timeout: int = 10) -> Any:
    """Try to run a function until a timeout is reached.

    Before the timeout is reached,
    all exceptions are ignored and a retry happens.
    """
    import time

    tstart = time.time()
    while (time.time() - tstart) < timeout:
        time.sleep(0.001)
        try:
            return fun()
        except Exception as e:
            pass
    return fun()


def _wait_until_server_is_up(server: dpf.server) -> Any:
    # Small hack to check if the server is up
    # The dpf server should check this in connect_to_server but that's currently not the case
    # https://github.com/pyansys/pydpf-core/issues/414
    # We use the fact that server.version throws if the server is not yet connected
    _try_until_timeout(lambda: server.version)


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

    all_composite_files = {}
    for key, composite_files_by_scope in data_files.composite.items():
        composite_definition_files = CompositeDefinitionFiles(
            definition=upload(composite_files_by_scope.definition),
        )

        if composite_files_by_scope.mapping is not None:
            composite_definition_files.mapping = upload(composite_files_by_scope.mapping)

        all_composite_files[key] = composite_definition_files

    return ContinuousFiberCompositesFiles(
        rst=upload(data_files.rst),
        engineering_data=upload(data_files.engineering_data),
        composite=all_composite_files,
    )


@dataclass
class _ContinuousFiberCompositeFiles:
    definition: str
    mapping: Optional[str] = None


@dataclass
class _ContinuousFiberCompositesExampleFilenames:
    rst: str
    composite: Dict[str, _ContinuousFiberCompositeFiles]
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
            composite={
                "shell": _ContinuousFiberCompositeFiles(
                    definition="ACPCompositeDefinitions.h5",
                )
            },
        ),
    ),
    "ins": _ContinuousFiberExampleLocation(
        directory="ins",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="beam_181_analysis_model.rst",
            engineering_data="materials.xml",
            composite={
                "shell": _ContinuousFiberCompositeFiles(definition="ACPCompositeDefinitions.h5")
            },
        ),
    ),
    "assembly": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=_ContinuousFiberCompositesExampleFilenames(
            rst="file.rst",
            engineering_data="material.engd",
            composite={
                "solid": _ContinuousFiberCompositeFiles(
                    definition="ACPSolidModel_SM.h5", mapping="ACPSolidModel_SM.mapping"
                ),
                "shell": _ContinuousFiberCompositeFiles(
                    definition="ACPCompositeDefinitions.h5",
                    mapping="ACPCompositeDefinitions.mapping",
                ),
            },
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


def connect_to_or_start_server(
    port: Optional[int] = None, ansys_path: Optional[str] = None
) -> ServerContext:
    """Connect to or start a dpf server."""
    port_in_env = os.environ.get("PYDPF_COMPOSITES_DOCKER_CONTAINER_PORT")
    if port_in_env is not None:
        port = int(port_in_env)

    if port is not None:
        server = dpf.server.connect_to_server("127.0.0.1", port=port)
    else:
        server = dpf.server.start_local_server(ansys_path=ansys_path)

    _wait_until_server_is_up(server)
    # Note: server.ansys_path contains the computed ansys path from
    # dpf.server.start_local_server. It is None if
    # we connect to an existing server.
    load_composites_plugin(server, ansys_path=server.ansys_path)
    return ServerContext(server=server)


def _get_file_url(directory: str, filename: str) -> str:
    return EXAMPLE_REPO + "/".join([directory, filename])


def _download_and_upload_file(
    directory: str, filename: str, tmpdir: str, server: dpf.server
) -> str:
    """Download example file from example_data repo and and upload it the the dpf server."""
    file_url = _get_file_url(directory, filename)
    local_path = os.path.join(tmpdir, filename)
    if server.local_server:
        local_path = os.path.join(os.getcwd(), filename)
    urllib.request.urlretrieve(file_url, local_path)
    # todo: With 0.7.1 the server will have
    #  a boolean property 'local_server' that we can use to
    #  determine if files should be uploaded
    if server.local_server:
        return local_path
    return cast(str, dpf.upload_file_in_tmp_folder(local_path, server=server))


def get_short_fiber_example_files(
    server_context: ServerContext,
    example_key: str,
) -> ShortFiberCompositesFiles:
    """Get short fiber example file by example key."""
    example_files = _short_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def get_server_path(filename: str) -> str:
            return _download_and_upload_file(
                example_files.directory, filename, tmpdir, server_context.server
            )

        return ShortFiberCompositesFiles(
            rst=get_server_path(example_files.files.rst),
            dsdat=get_server_path(example_files.files.dsdat),
            engineering_data=get_server_path(example_files.files.engineering_data),
        )


def get_continuous_fiber_example_files(
    server_context: ServerContext,
    example_key: str,
) -> ContinuousFiberCompositesFiles:
    """Get continuous fiber example file by example key."""
    example_files = _continuous_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def get_sever_path(filename: str) -> str:
            return _download_and_upload_file(
                example_files.directory, filename, tmpdir, server_context.server
            )

        all_composite_files = {}
        for key, composite_examples_files_for_scope in example_files.files.composite.items():
            composite_files = CompositeDefinitionFiles(
                definition=get_sever_path(composite_examples_files_for_scope.definition),
            )
            if composite_examples_files_for_scope.mapping is not None:
                composite_files.mapping = get_sever_path(composite_examples_files_for_scope.mapping)

            all_composite_files[key] = composite_files

        return ContinuousFiberCompositesFiles(
            rst=get_sever_path(example_files.files.rst),
            engineering_data=get_sever_path(example_files.files.engineering_data),
            composite=all_composite_files,
        )
