from __future__ import annotations

from contextlib import closing
import os
import pathlib
import socket
import subprocess
import sys
from types import MappingProxyType
from typing import Mapping, Optional
import uuid

import pytest

TEST_ROOT_DIR = pathlib.Path(__file__).parent


class DockerWrapper:
    """Wraps a DPF docker container. The container is started on __init__

    stop cleans up all the resources and stops the container
    """

    def __init__(
        self,
        image_name: str = "ghcr.io/pyansys/pydpf-composites:latest",
        mount_directories: Mapping[str, str] = MappingProxyType({}),
        port: Optional[int] = None,
        server_out_file: _PATH = os.devnull,
        server_err_file: _PATH = os.devnull,
        process_out_file: _PATH = os.devnull,
        process_err_file: _PATH = os.devnull,
    ):
        """Start the docker container
        Parameters
        ----------
        image_name :
            The name of the Docker image to launch.
        mount_directories :
            Local directories which should be mounted to the Docker container.
            The keys contain the path in the context of the host, and the
            values are the paths as they should appear inside the container.
        server_out_file :
            Path (on the host) to which the output of ``docker run`` is redirected.
        server_err_file :
            Path (on the host) where the standard error of ``docker run`` is
            redirected.
        process_out_file :
            Path (on the host) to which additional log output for the python subprocess
            is redirected.
        process_err_file :
            Path (on the host) to which additional error output for the python subprocess
             is redirected.
        """
        if port is None:
            port = _find_free_port()
        self.server_stdout = open(server_out_file, mode="w", encoding="utf-8")
        self.server_stderr = open(server_err_file, mode="w", encoding="utf-8")

        self.process_stdout = open(process_out_file, mode="w", encoding="utf-8")
        self.process_stderr = open(process_err_file, mode="w", encoding="utf-8")
        self.name = str(uuid.uuid4())

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
            "--name",
            self.name,
            image_name,
        ]
        self.process_stdout.write(f"Starting docker container: {cmd}\n\n")
        self.server_process = subprocess.Popen(
            cmd,
            stdout=self.server_stdout,
            stderr=self.server_stderr,
            text=True,
        )
        # Todo: Check if server is up differently
        import time

        time.sleep(3)
        self.process_stdout.write(f"Output of docker ps after start\n")
        out = subprocess.check_output(["docker", "ps"])
        self.process_stdout.write(str(out))
        self.process_stdout.write(f"\n\n")

    def stop(self):
        out = subprocess.check_output(["docker", "stop", self.name])
        self.process_stdout.write(str(out))

        self.process_stdout.write(f"docker ps after stopping the container:\n")
        self.process_stdout.write(f"\n")
        out = subprocess.check_output(["docker", "ps"])
        self.process_stdout.write(str(out))
        self.process_stdout.write(f"\n")

        self.server_process.communicate()

        self.server_stdout.close()
        self.server_stderr.close()
        self.process_stdout.close()
        self.process_stderr.close()


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

    process_log_stdout = TEST_ROOT_DIR / "process_log_out.txt"
    process_log_stderr = TEST_ROOT_DIR / "process_log_err.txt"
    wrapper = None
    try:
        wrapper = DockerWrapper(
            server_out_file=server_log_stdout,
            server_err_file=server_log_stderr,
            process_out_file=process_log_stdout,
            process_err_file=process_log_stderr,
            port=port,
        )

        import ansys.dpf.core as dpf

        server = dpf.server.connect_to_server("127.0.0.1", port=port)

        dpf.load_library("libcomposite_operators.so", "composites", server=server)
        dpf.load_library("libAns.Dpf.EngineeringData.so", "engineeringdata", server=server)
        yield server
    finally:
        if wrapper is not None:
            wrapper.stop()
