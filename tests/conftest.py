from __future__ import annotations

from collections import namedtuple
from contextlib import closing
import os
import pathlib
import socket
import subprocess
import sys
from types import MappingProxyType
from typing import Mapping
import uuid

import ansys.dpf.core as dpf
import pytest

from ansys.dpf.composites.load_plugin import load_composites_plugin

TEST_ROOT_DIR = pathlib.Path(__file__).parent

SERVER_BIN_OPTION_KEY = "--server-bin"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    parser.addoption(
        SERVER_BIN_OPTION_KEY,
        action="store",
        help="Path of the dpf server executable",
    )


ServerContext = namedtuple("ServerContext", ["port", "platform"])


class DockerProcess:
    """Context manager that wraps a docker process"""

    def __enter__(self):
        cmd = ["docker", "run"]
        for source_dir, target_dir in self.mount_directories.items():
            cmd += ["-v", f"/{pathlib.Path(source_dir).as_posix().replace(':', '')}:{target_dir}"]
        if sys.platform == "linux":
            cmd += ["-u", f"{os.getuid()}:{os.getgid()}"]
        cmd += [
            "-p",
            f"{self.port}:50052/tcp",
            "-e",
            "HOME=/home/container",
            "--name",
            self.name,
            self.image_name,
        ]
        self.process_stdout.write(f"Starting docker container: {cmd}\n\n")
        self.server_process = subprocess.Popen(
            cmd,
            stdout=self.server_stdout,
            stderr=self.server_stderr,
            text=True,
        )

        self.process_stdout.write(f"Output of docker ps after start\n")
        out = subprocess.check_output(["docker", "ps"])
        self.process_stdout.write(str(out))
        self.process_stdout.write(f"\n\n")

        return ServerContext(port=self.port, platform="linux")

    def __init__(
        self,
        server_out_file: pathlib.Path,
        server_err_file: pathlib.Path,
        process_out_file: pathlib.Path,
        process_err_file: pathlib.Path,
        image_name: str = "ghcr.io/pyansys/pydpf-composites:latest",
        mount_directories: Mapping[str, str] = MappingProxyType({}),
    ):
        """Initialize the wrapper
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
        self.port = _find_free_port()
        self.server_stdout = open(server_out_file, mode="w", encoding="utf-8")
        self.server_stderr = open(server_err_file, mode="w", encoding="utf-8")

        self.process_stdout = open(process_out_file, mode="w", encoding="utf-8")
        self.process_stderr = open(process_err_file, mode="w", encoding="utf-8")
        self.name = str(uuid.uuid4())
        self.mount_directories = mount_directories
        self.image_name = image_name

    def __exit__(
        self,
        type,
        value,
        traceback,
    ):
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


class LocalServerProcess:
    """Context manager that wraps a local server executable"""

    def __init__(
        self,
        server_executable: str,
        server_out_file: pathlib.Path,
        server_err_file: pathlib.Path,
    ):
        """Initialize the wrapper
        Parameters
        ----------
        server_executable :
            Path
        server_out_file :
            Path where the standard out of the server is
            redirected.
        server_err_file :
            Path where the standard error of the server is
            redirected.
        """
        self.port = _find_free_port()
        self.server_stdout = open(server_out_file, mode="w", encoding="utf-8")
        self.server_stderr = open(server_err_file, mode="w", encoding="utf-8")

        self.server_executable = server_executable

        if sys.platform != "win32":
            raise Exception(
                "Local server currently not supported on linux. Please use the docker container"
            )
        self.env = os.environ.copy()
        # Add parent folder of deps to path which contains the composites operators
        self.env["PATH"] = (
            self.env["PATH"] + ";" + str(pathlib.Path(self.server_executable).parent.parent)
        )

    def __enter__(self):
        cmd = [self.server_executable, "--port", str(self.port), "--address", dpf.server.LOCALHOST]
        self.server_process = subprocess.Popen(
            cmd, stdout=self.server_stdout, stderr=self.server_stderr, text=True, env=self.env
        )

        return ServerContext(port=self.port, platform=sys.platform)

    def __exit__(
        self,
        type,
        value,
        traceback,
    ):
        self.server_process.kill()
        self.server_process.communicate(timeout=5)

        self.server_stdout.close()
        self.server_stderr.close()


def _find_free_port() -> int:
    """Find a free port on localhost.

    .. note::

        There is no guarantee that the port is *still* free when it is
        used by the calling code.
    """
    with closing(socket.socket()) as sock:
        sock.bind(("", 0))  # bind to a free port
        return sock.getsockname()[1]  # type: ignore


def wait_until_server_is_up(server):
    # Small hack to check if the server is up
    # The dpf server should check this in connect_to_server but that's currently not the case
    # https://github.com/pyansys/pydpf-core/issues/414
    # We use the fact that server.version throws if the server is not yet connected
    timeout = 5
    import time

    tstart = time.time()
    while (time.time() - tstart) < timeout:
        time.sleep(0.001)
        try:
            server.version
            break
        except Exception as e:
            pass
    server.version


@pytest.fixture(scope="session")
def dpf_server(request: pytest.FixtureRequest):
    server_log_stdout = TEST_ROOT_DIR / "server_log_out.txt"
    server_log_stderr = TEST_ROOT_DIR / "server_log_err.txt"

    server_bin = request.config.getoption(SERVER_BIN_OPTION_KEY)

    def start_server_process():
        if server_bin:
            return LocalServerProcess(
                server_bin, server_out_file=server_log_stdout, server_err_file=server_log_stderr
            )
        else:
            process_log_stdout = TEST_ROOT_DIR / "process_log_out.txt"
            process_log_stderr = TEST_ROOT_DIR / "process_log_err.txt"
            return DockerProcess(
                server_out_file=server_log_stdout,
                server_err_file=server_log_stderr,
                process_out_file=process_log_stdout,
                process_err_file=process_log_stderr,
            )

    with start_server_process() as server_process:
        server = dpf.server.connect_to_server(port=server_process.port)

        wait_until_server_is_up(server)
        load_composites_plugin(platform=server_process.platform, server=server)

        yield server
