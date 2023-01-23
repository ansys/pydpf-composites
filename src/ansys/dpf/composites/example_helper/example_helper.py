"""Helper to get example files."""

from dataclasses import dataclass
import os
import tempfile
from typing import Dict, cast
import urllib.request

import ansys.dpf.core as dpf

from .._typing_helper import PATH as _PATH
from ..composite_data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
)

EXAMPLE_REPO = "https://github.com/pyansys/example-data/raw/master/pydpf-composites/"


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
    files: ContinuousFiberCompositesFiles


@dataclass
class _ShortFiberExampleLocation:
    """Location of a given short fiber example in the example_data repo.

    Parameters
    ----------
    directory:
        Directory in example_data/pydpf-composites
    files:
        Example files in directory
    """

    directory: str
    files: ShortFiberCompositesFiles


_continuous_fiber_examples: Dict[str, _ContinuousFiberExampleLocation] = {
    "shell": _ContinuousFiberExampleLocation(
        directory="shell",
        files=ContinuousFiberCompositesFiles(
            rst="shell.rst",
            engineering_data="material.engd",
            composite={
                "shell": CompositeDefinitionFiles(
                    definition="ACPCompositeDefinitions.h5",
                )
            },
        ),
    ),
    "ins": _ContinuousFiberExampleLocation(
        directory="ins",
        files=ContinuousFiberCompositesFiles(
            rst="beam_181_analysis_model.rst",
            engineering_data="materials.xml",
            composite={"shell": CompositeDefinitionFiles(definition="ACPCompositeDefinitions.h5")},
        ),
    ),
    "assembly": _ContinuousFiberExampleLocation(
        directory="assembly",
        files=ContinuousFiberCompositesFiles(
            rst="file.rst",
            engineering_data="material.engd",
            composite={
                "solid": CompositeDefinitionFiles(
                    definition="ACPSolidModel_SM.h5", mapping="ACPSolidModel_SM.mapping"
                ),
                "shell": CompositeDefinitionFiles(
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
        files=ShortFiberCompositesFiles(
            rst="file.rst", engineering_data="MatML.xml", dsdat="ds.dat"
        ),
    )
}


def _get_file_url(directory: str, filename: _PATH) -> _PATH:
    return EXAMPLE_REPO + "/".join([directory, filename])


def _download_and_upload_file(
    directory: str, filename: _PATH, tmpdir: str, server: dpf.server
) -> _PATH:
    """Download example file from example_data repo and upload it the dpf server."""
    file_url = _get_file_url(directory, filename)
    local_path = os.path.join(tmpdir, filename)
    if server.local_server:
        local_path = os.path.join(os.getcwd(), filename)
    urllib.request.urlretrieve(file_url, local_path)
    if server.local_server:
        return local_path
    return cast(_PATH, dpf.upload_file_in_tmp_folder(local_path, server=server))


def get_short_fiber_example_files(
    server: dpf.server,
    example_key: str,
) -> ShortFiberCompositesFiles:
    """Get short fiber example file by example key.

    This will copy the example files into the current working directory, if the
    server is local.

    Parameters
    ----------
    server:
    example_key:
    """
    example_files = _short_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def get_server_path(filename: _PATH) -> _PATH:
            return _download_and_upload_file(example_files.directory, filename, tmpdir, server)

        return ShortFiberCompositesFiles(
            rst=get_server_path(example_files.files.rst),
            dsdat=get_server_path(example_files.files.dsdat),
            engineering_data=get_server_path(example_files.files.engineering_data),
        )


def get_continuous_fiber_example_files(
    server: dpf.server,
    example_key: str,
) -> ContinuousFiberCompositesFiles:
    """Get continuous fiber example file by example key.

    This will copy the example files into the current working directory, if the
    server is local.

    Parameters
    ----------
    server:
    example_key:
    """
    example_files = _continuous_fiber_examples[example_key]
    with tempfile.TemporaryDirectory() as tmpdir:

        def get_server_path(filename: _PATH) -> _PATH:
            return _download_and_upload_file(example_files.directory, filename, tmpdir, server)

        all_composite_files = {}
        for key, composite_examples_files_for_scope in example_files.files.composite.items():
            composite_files = CompositeDefinitionFiles(
                definition=get_server_path(composite_examples_files_for_scope.definition),
            )
            if composite_examples_files_for_scope.mapping is not None:
                composite_files.mapping = get_server_path(
                    composite_examples_files_for_scope.mapping
                )

            all_composite_files[key] = composite_files

        return ContinuousFiberCompositesFiles(
            rst=get_server_path(example_files.files.rst),
            engineering_data=get_server_path(example_files.files.engineering_data),
            composite=all_composite_files,
        )
