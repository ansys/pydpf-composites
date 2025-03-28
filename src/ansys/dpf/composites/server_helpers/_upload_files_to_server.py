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

import os
import pathlib
from typing import cast
import uuid

import ansys.dpf.core as dpf
from ansys.dpf.core.server_types import BaseServer

from .._typing_helper import PATH as _PATH
from ..constants import D3PLOT_KEY_AND_FILENAME, SolverType
from ..data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
    get_d3plot_from_list_of_paths,
)


def _get_all_files_in_folder(directory: _PATH, key: str = "") -> list[_PATH]:
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory {directory} not found.")

    paths: list[_PATH] = []
    for root, _, files in os.walk(directory):
        paths.extend([os.path.join(root, file_name) for file_name in files if key in file_name])

    return paths


def _construct_path_on_server(
    tmp_dir: _PATH, server: BaseServer, my_uuid: str, file_name: str
) -> str:
    if server.os == "posix":
        path_on_server = str(tmp_dir) + "/" + my_uuid + "/" + file_name
    else:
        path_on_server = str(tmp_dir) + "\\" + my_uuid + "\\" + file_name
    return path_on_server


def _get_path_on_server_from_tmpdir(
    tmp_dir: _PATH, path_on_client: _PATH, server: BaseServer, my_uuid: str
) -> str:
    # construct an unique path on the server like /tmp/<tmp_dir>/<my_uuid>/filename
    path_on_client = pathlib.Path(path_on_client)
    return _construct_path_on_server(tmp_dir, server, my_uuid, path_on_client.name)


def _get_path_on_server(path_on_client: _PATH, server: BaseServer) -> str:
    # construct an unique path on the server like /tmp/<temporary dir>/<uuid>/filename
    tmp_dir = dpf.make_tmp_dir_server(server)
    return _get_path_on_server_from_tmpdir(tmp_dir, path_on_client, server, str(uuid.uuid4()))


def upload_file_to_unique_tmp_folder(path_on_client: _PATH, server: BaseServer) -> str:
    """Upload file to a unique temporary folder on the server.

    Parameters
    ----------
    path_on_client:
        Client side path of the file which should be uploaded to the server.
    server:
        DPF server.
    """
    path_on_server = _get_path_on_server(path_on_client, server)
    uploaded_path = cast(str, dpf.upload_file(path_on_client, path_on_server, server=server))
    if uploaded_path == "":
        raise RuntimeError(
            f"Failed to upload file {path_on_client} to server. "
            f"Attempted to upload to {path_on_server}."
        )
    return uploaded_path


def upload_files_to_unique_tmp_folder(
    paths_on_client: list[_PATH], server: BaseServer
) -> list[_PATH]:
    """Upload files to the same unique temporary folder on the server.

    Parameters
    ----------
    paths_on_client:
        List of files which have to be uploaded to one tmp folder on the server.
    server:
        DPF server.
    """
    paths_on_server: list[_PATH] = []
    tmp_dir = dpf.make_tmp_dir_server(server)
    my_uuid = str(uuid.uuid4())
    for file_path in paths_on_client:
        file_path = pathlib.Path(file_path)
        path_on_server = _get_path_on_server_from_tmpdir(tmp_dir, file_path, server, my_uuid)
        uploaded_path = cast(str, dpf.upload_file(file_path, path_on_server, server=server))
        if uploaded_path == "":
            raise RuntimeError(
                f"Failed to upload file {file_path} to server. "
                f"Attempted to upload to {path_on_server}."
            )
        paths_on_server.append(uploaded_path)
    return paths_on_server


def upload_short_fiber_composite_files_to_server(
    data_files: ShortFiberCompositesFiles, server: BaseServer
) -> ShortFiberCompositesFiles:
    """Upload short fiber composites files to server.

    Parameters
    ----------
    data_files
    server
    """
    # If files are not local, it means they have already been
    # uploaded to the server
    if server.local_server or not data_files.files_are_local:
        return data_files

    def upload(filename: _PATH) -> str:
        return upload_file_to_unique_tmp_folder(filename, server=server)

    return ShortFiberCompositesFiles(
        rst=[upload(filename) for filename in data_files.rst],
        dsdat=upload(data_files.dsdat),
        engineering_data=upload(data_files.engineering_data),
        files_are_local=False,
    )


def upload_continuous_fiber_composite_files_to_server(
    data_files: ContinuousFiberCompositesFiles, server: BaseServer
) -> ContinuousFiberCompositesFiles:
    """Upload continuous fiber composites files to server.

    Note: If server.local_server == True the data_files are returned unmodified.

    Parameters
    ----------
    data_files
        All input files such as result files, material file etc.
    server
        A running DPF server (in process or remote).
    """
    # If files are not local, it means they have already been
    # uploaded to the server
    if server.local_server or not data_files.files_are_local:
        return data_files

    def upload(filename: _PATH) -> _PATH:
        return upload_file_to_unique_tmp_folder(filename, server=server)

    all_composite_files = {}
    for key, composite_files_by_scope in data_files.composite.items():
        composite_definition_files = CompositeDefinitionFiles(
            definition=upload(composite_files_by_scope.definition),
        )
        if composite_files_by_scope.mapping is not None:
            composite_definition_files.mapping = upload(composite_files_by_scope.mapping)
        all_composite_files[key] = composite_definition_files

    rst_file_paths_on_server: list[_PATH] = []

    # Copy all d3plot files (d3plot01, d3plot02, ...) to the server
    if data_files.solver_type == SolverType.LSDYNA:
        # all d3plot files have to be uploaded to the same folder. Note, only the d3plot
        # format of LSDyna is currently supported
        all_d3plot_files = _get_all_files_in_folder(
            os.path.dirname(data_files.result_files[0]), D3PLOT_KEY_AND_FILENAME
        )
        # The LSDyna reader automatically picks up the additional d3plot files and so only the first
        # one is passed to the DPF datasource.
        all_d3plot_paths_on_server = upload_files_to_unique_tmp_folder(
            all_d3plot_files, server=server
        )
        rst_file_paths_on_server = [get_d3plot_from_list_of_paths(all_d3plot_paths_on_server)]
    else:
        rst_file_paths_on_server = [upload(filename) for filename in data_files.result_files]

    return ContinuousFiberCompositesFiles(
        result_files=rst_file_paths_on_server,
        engineering_data=upload(data_files.engineering_data),
        composite=all_composite_files,
        solver_input_file=(
            upload(data_files.solver_input_file) if data_files.solver_input_file else None
        ),
        files_are_local=False,
        solver_type=data_files.solver_type,
    )
