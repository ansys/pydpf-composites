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
from collections.abc import Callable
import os
from typing import Any

from ansys.dpf.core import connect_to_server
from ansys.dpf.core import server as _dpf_server
from ansys.dpf.core import start_local_server

from ansys.dpf.composites.server_helpers._load_plugin import load_composites_plugin


def _try_until_timeout(fun: Callable[[], Any], error_message: str, timeout: int = 10) -> Any:
    """Try to run a function until a timeout is reached.

    Before the timeout is reached, all exceptions are ignored and a retry happens.
    """
    import time

    tstart = time.time()
    while (time.time() - tstart) < timeout:
        time.sleep(0.001)
        try:
            return fun()
        except Exception:  # pylint: disable=broad-except
            pass
    raise TimeoutError(f"Timeout is reached: {error_message}")


def _wait_until_server_is_up(server: _dpf_server) -> Any:
    # Small hack to check if the server is up.
    # The DPF server should check this in the ``connect_to_server`` function, but
    # that's currently not the case.
    # https://github.com/ansys/pydpf-core/issues/414
    # We use the fact that server.version throws an error if the server
    # is not yet connected.
    _try_until_timeout(
        lambda: server.version, "Failed to connect to the DPF server before timing out."
    )


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

    _wait_until_server_is_up(server)
    # Note: server.ansys_path contains the computed Ansys path from
    # dpf.server.start_local_server. It is None if
    # a connection is made to an existing server.
    load_composites_plugin(server, ansys_path=server.ansys_path)
    return server
