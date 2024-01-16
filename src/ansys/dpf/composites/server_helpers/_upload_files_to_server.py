# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import pathlib
from typing import cast
import uuid

import ansys.dpf.core as dpf
from ansys.dpf.core.server_types import BaseServer

from .._typing_helper import PATH as _PATH
from ..data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
)


def upload_file_to_unique_tmp_folder(path_on_client: _PATH, server: BaseServer) -> str:
    """Upload file to a unique temporary folder on the server.

    Parameters
    ----------
    path_on_client:
        Client side path of the file which should be uploaded to the server.
    server:
        DPF server.
    """
    tmp_dir = pathlib.Path(
        dpf.make_tmp_dir_server()
    )  # Returns the dpf tmp folder (only one per server)
    path_on_client = pathlib.Path(path_on_client)
    if server.os == "posix":
        path_on_server = str(tmp_dir) + "/" + str(uuid.uuid4()) + "/" + path_on_client.name
    else:
        path_on_server = str(tmp_dir) + "\\" + str(uuid.uuid4()) + "\\" + path_on_client.name

    uploaded_path = cast(str, dpf.upload_file(path_on_client, path_on_server, server=server))
    if uploaded_path == "":
        raise RuntimeError(
            f"Failed to upload file {path_on_client} to server. "
            f"Attempted to upload to {path_on_server}."
        )
    return uploaded_path


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
    server
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

    return ContinuousFiberCompositesFiles(
        rst=[upload(filename) for filename in data_files.rst],
        engineering_data=upload(data_files.engineering_data),
        composite=all_composite_files,
        files_are_local=False,
    )
