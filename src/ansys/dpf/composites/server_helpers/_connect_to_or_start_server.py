"""Helpers to connect to or start a dpf server with the composites plugin."""
import os
from typing import Any, Callable, Dict, Optional, Union

import ansys.dpf.core as dpf

from ansys.dpf.composites.server_helpers._load_plugin import load_composites_plugin


def _try_until_timeout(fun: Callable[[], Any], error_message: str, timeout: int = 10) -> Any:
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
        except Exception:  # pylint: disable=broad-except
            pass
    raise TimeoutError(f"Timeout is reached: {error_message}")


def _wait_until_server_is_up(server: dpf.server) -> Any:
    # Small hack to check if the server is up
    # The dpf server should check this in connect_to_server but that's currently not the case
    # https://github.com/pyansys/pydpf-core/issues/414
    # We use the fact that server.version throws if the server is not yet connected
    _try_until_timeout(lambda: server.version, "Failed to connect to server before timeout.")


def connect_to_or_start_server(
    port: Optional[int] = None, ip: Optional[str] = None, ansys_path: Optional[str] = None
) -> dpf.server:
    r"""Connect to or start a dpf server with the composites plugin loaded.

    Note: If port or ip are set, this function will try to
    connect to a server and the ansys_path is ignored.
    I no arguments are passed a local server from the latest available installer
    is started.

    Parameters
    ----------
    port:
    ip:
    ansys_path:
        Ansys root path, for example C:\Program Files\ANSYS Inc\v231.
        Ignored if either port or ip are set.
    """
    port_in_env = os.environ.get("PYDPF_COMPOSITES_DOCKER_CONTAINER_PORT")
    if port_in_env is not None:
        port = int(port_in_env)

    connect_kwargs: Dict[str, Union[int, str]] = {}
    if port is not None:
        connect_kwargs["port"] = port
    if ip is not None:
        connect_kwargs["ip"] = ip

    if len(list(connect_kwargs.keys())) > 0:
        server = dpf.server.connect_to_server(**connect_kwargs)
    else:
        server = dpf.server.start_local_server(ansys_path=ansys_path)

    server.check_version(
        "5.0",
        f"The composites plugin requires at least server version 5.0 (Ansys 2023R1)"
        f" Your version is currently {server.version}",
    )

    _wait_until_server_is_up(server)
    # Note: server.ansys_path contains the computed ansys path from
    # dpf.server.start_local_server. It is None if
    # we connect to an existing server.
    load_composites_plugin(server, ansys_path=server.ansys_path)
    return server
