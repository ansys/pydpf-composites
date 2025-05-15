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

"""Helpers to connect to or start a DPF server with the DPF Composites plugin."""
import os
from typing import Any

from ansys.dpf.core import connect_to_server, start_local_server

from ansys.dpf.composites.server_helpers._load_plugin import load_composites_plugin


def connect_to_or_start_server(
    port: int | None = None, ip: str | None = None, ansys_path: str | None = None
) -> Any:
    r"""Connect to or start a DPF server with the DPF Composites plugin loaded.

    .. note::

        If a port or IP address is set, this method tries to connect to the server specified
        and the ``ansys_path`` parameter is ignored. If no parameters are set, a local server
        from the latest available Ansys installation is started.

    Parameters
    ----------
    port :
        Port that the DPF server is listening on.
    ip :
        IP address for the DPF server.
    ansys_path :
        Root path for the Ansys installation. For example, ``C:\\Program Files\\ANSYS Inc\\v232``.
        This parameter is ignored if either the port or IP address is set.

    Returns
    -------
    :
        DPF server.
    """
    port_in_env = os.environ.get("PYDPF_COMPOSITES_DOCKER_CONTAINER_PORT")
    if port_in_env is not None:
        port = int(port_in_env)

    connect_kwargs: dict[str, int | str] = {}
    if port is not None:
        connect_kwargs["port"] = port
    if ip is not None:
        connect_kwargs["ip"] = ip

    if len(list(connect_kwargs.keys())) > 0:
        server = connect_to_server(
            **connect_kwargs,
        )
    else:
        server = start_local_server(
            ansys_path=ansys_path,
        )

    required_version = "6.0"
    server.check_version(
        required_version,
        f"The DPF Composites plugin requires DPF Server version {required_version} "
        f"(Ansys 2023 R2) or later. Your version is currently {server.version}.",
    )

    # Note: server.ansys_path contains the computed Ansys path from
    # dpf.server.start_local_server. It is None if
    # a connection is made to an existing server.
    load_composites_plugin(server, ansys_path=server.ansys_path)
    return server
