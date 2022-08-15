from __future__ import annotations

from contextlib import closing
import os
import pathlib
import socket
import subprocess
import sys
from types import MappingProxyType
from typing import Any, Mapping, Optional, TextIO
import weakref

import pytest


class ProcessWrapper:
    """Manages a process running on the local machine.

    Wrapper for a process.
    This class takes care of terminating the process when the object is
    either destroyed, or before Python exits (unless it is a hard crash
    / kill).
    Can be used as a context manager, to terminate the process when
    exiting the context.

    Parameters
    ----------
    process :
        The wrapped process
    stdout :
        Open file handle to which the process output is being written.
    stderr :
        Open file handle to which the process error is being written.
    """

    def __init__(self, process: subprocess.Popen[str], stdout: TextIO, stderr: TextIO):
        self._process = process
        self._stdout = stdout
        self._stderr = stderr

        self._finalizer = weakref.finalize(
            self,
            self._finalize_impl,
            process=self._process,
            stdout=self._stdout,
            stderr=self._stderr,
        )

    @staticmethod
    def _finalize_impl(process: subprocess.Popen[str], stdout: TextIO, stderr: TextIO) -> None:
        process.terminate()
        process.wait()
        stdout.close()
        stderr.close()

    # Todo: This does not kill the docker process. We have to stop it with docker stop

    def __enter__(self) -> ProcessWrapper:
        return self

    def __exit__(self, *exc: Any) -> None:
        self._finalizer()


def launch_dpf_docker(
    *,
    image_name: str = "ghcr.io/pyansys/pydpf-composites:latest",
    mount_directories: Mapping[str, str] = MappingProxyType({}),
    port: Optional[int] = None,
    stdout_file: _PATH = os.devnull,
    stderr_file: _PATH = os.devnull,
) -> ServerProtocol:
    """Launch an ACP server locally in a Docker container.

    Use ``docker run`` to locally start an ACP Docker container.

    Parameters
    ----------
    image_name :
        The name of the Docker image to launch.
    mount_directories :
        Local directories which should be mounted to the Docker container.
        The keys contain the path in the context of the host, and the
        values are the paths as they should appear inside the container.
    stdout_file :
        Path (on the host) to which the output of ``docker run`` is redirected.
    stderr_file :
        Path (on the host) where the standard error of ``docker run`` is
        redirected.

    Returns
    -------
    :
        ProcessWrapper
    """
    if port is None:
        port = _find_free_port()
    stdout = open(stdout_file, mode="w", encoding="utf-8")
    stderr = open(stderr_file, mode="w", encoding="utf-8")
    cmd = ["docker", "run"]
    for source_dir, target_dir in mount_directories.items():
        cmd += ["-v", f"/{pathlib.Path(source_dir).as_posix().replace(':', '')}:{target_dir}"]
    if sys.platform == "linux":
        cmd += ["-u", f"{os.getuid()}:{os.getgid()}"]
    cmd += [
        "-p",
        f"{port}:50052/tcp",
        "-e",
        "HOME=/home/container",
        image_name,
    ]
    process = subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        text=True,
    )
    return ProcessWrapper(process=process, stdout=stdout, stderr=stderr)


TEST_ROOT_DIR = pathlib.Path(__file__).parent


def _find_free_port() -> int:
    """Find a free port on localhost.

    .. note::

        There is no guarantee that the port is *still* free when it is
        used by the calling code.
    """
    with closing(socket.socket()) as sock:
        sock.bind(("", 0))  # bind to a free port
        return sock.getsockname()[1]  # type: ignore


@pytest.fixture(scope="session")
def dpf_server():
    port = _find_free_port()
    server_log_stdout = TEST_ROOT_DIR / "server_log_out.txt"
    server_log_stderr = TEST_ROOT_DIR / "server_log_err.txt"
    with launch_dpf_docker(
        stdout_file=server_log_stdout, stderr_file=server_log_stderr, port=port
    ) as process_wrapper:

        import ansys.dpf.core as dpf

        server = dpf.server.connect_to_server("127.0.0.1", port=port)

        dpf.load_library("libcomposite_operators.so", "composites", server=server)
        dpf.load_library("libAns.Dpf.EngineeringData.so", "engineeringdata", server=server)
        yield server
