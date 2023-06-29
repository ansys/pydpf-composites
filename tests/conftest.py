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

from ansys.dpf.composites.server_helpers._connect_to_or_start_server import (
    _try_until_timeout,
    _wait_until_server_is_up,
)
from ansys.dpf.composites.server_helpers._load_plugin import load_composites_plugin
from ansys.dpf.composites.server_helpers._versions import version_equal_or_later

TEST_ROOT_DIR = pathlib.Path(__file__).parent

PORT_OPTION_KEY = "--port"
ANSYS_PATH_OPTION_KEY = "--ansys-path"
LICENSE_SERVER_OPTION_KEY = "--license-server"
ANSYSLMD_LICENSE_FILE_KEY = "ANSYSLMD_LICENSE_FILE"
DOCKER_IMAGE_TAG_KEY = "--image-tag"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""

    parser.addoption(
        PORT_OPTION_KEY,
        action="store",
        help="Port of an already running dpf server. "
        "Can be used to test with a debug container. Only supported for linux containers.",
    )

    parser.addoption(
        ANSYS_PATH_OPTION_KEY,
        action="store",
        help="If set, the dpf server is started from an ansys location located at the given path."
        r"Example: C:\Program Files\Ansys Inc\v231",
    )

    parser.addoption(
        LICENSE_SERVER_OPTION_KEY,
        action="store",
        help="Value of the ANSYSLMD_LICENSE_FILE for the gRPC server.",
    )

    parser.addoption(
        DOCKER_IMAGE_TAG_KEY,
        action="store",
        default="latest",
        help="Tag of pydpf-composites container to start for the tests. Default is 'latest'.",
    )


ServerContext = namedtuple("ServerContext", ["port", "platform", "server"])


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
            "HOME=/tmp",
            "-e",
            "ANSYS_DPF_ACCEPT_LA=Y",
            "-e",
            f"{ANSYSLMD_LICENSE_FILE_KEY}={self.license_server}",
            "--name",
            self.name,
            self.image_name,
        ]
        # ensure that the output does not contain any pipeline secrets
        # self.process_stdout.write(f"Starting docker container: {cmd}\n\n")
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

        return ServerContext(port=self.port, platform="linux", server=None)

    def __init__(
        self,
        server_out_file: pathlib.Path,
        server_err_file: pathlib.Path,
        process_out_file: pathlib.Path,
        process_err_file: pathlib.Path,
        license_server: str = "",
        image_name: str = "",
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
        license_server:
            Definition of the license server. E.g. 1055@my_ansys_license_server
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
        self.license_server = license_server
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


class RunningServer:
    """Context manager that wraps an already running dpf server that serves at a port"""

    def __init__(self, port: str, platform: str = "linux"):
        self.port = port
        self.platform = platform

    def __enter__(self):
        return ServerContext(port=self.port, platform=self.platform, server=None)

    def __exit__(self, *args):
        pass


class InstalledServer:
    """Context manager that wraps a dpf server started from the installer"""

    def __init__(self, ansys_path: str):
        self.ansys_path = ansys_path

    def __enter__(self):
        context = dpf.server.server_context.ServerContext(
            dpf.server_context.LicensingContextType.premium
        )

        server = dpf.start_local_server(ansys_path=self.ansys_path, context=context)
        return ServerContext(port=None, platform=sys.platform, server=server)

    def __exit__(self, *args):
        pass


def _find_free_port() -> int:
    """Find a free port on localhost.

    .. note::

        There is no guarantee that the port is *still* free when it is
        used by the calling code.
    """
    with closing(socket.socket()) as sock:
        sock.bind(("", 0))  # bind to a free port
        return sock.getsockname()[1]  # type: ignore


def prepend_port_if_needed(license_server):
    if "@" not in license_server:
        license_server = "1055@" + license_server
    return license_server


def get_license_server_string(license_server_option: str) -> str | None:
    if license_server_option:
        return prepend_port_if_needed(license_server_option)
    if ANSYSLMD_LICENSE_FILE_KEY in os.environ.keys():
        return prepend_port_if_needed(os.environ[ANSYSLMD_LICENSE_FILE_KEY])

    raise RuntimeError(
        "License server not set. Either run test with --license-server or "
        f" set ENV {ANSYSLMD_LICENSE_FILE_KEY}."
    )


@pytest.fixture(scope="session")
def dpf_server(request: pytest.FixtureRequest):
    # Use a unique session id so logs don't get overwritten
    # by tests that run in different sessions
    import uuid

    uid = uuid.uuid4()
    if not os.path.exists(TEST_ROOT_DIR / "logs"):
        os.mkdir(TEST_ROOT_DIR / "logs")
    server_log_stdout = TEST_ROOT_DIR / "logs" / f"server_log_out-{uid}.txt"
    server_log_stderr = TEST_ROOT_DIR / "logs" / f"server_log_err-{uid}.txt"

    running_server_port = request.config.getoption(PORT_OPTION_KEY)
    installer_path = request.config.getoption(ANSYS_PATH_OPTION_KEY)
    license_server_config = request.config.getoption(LICENSE_SERVER_OPTION_KEY)
    docker_image_tag = request.config.getoption(DOCKER_IMAGE_TAG_KEY)

    active_options = [
        option
        for option in [installer_path, running_server_port, docker_image_tag]
        if option is not None
    ]

    if len(active_options) > 1:
        if (docker_image_tag is not None) and docker_image_tag == "latest":
            # We don't want to fail if docker_image_tag is not set explicitly
            # because it has a default value.
            docker_image_tag = None
        else:
            raise Exception(f"Invalid inputs. Multiple options specified: {active_options}")

    def start_server_process():
        if running_server_port:
            return RunningServer(port=running_server_port)
        if installer_path:
            return InstalledServer(installer_path)
        else:
            process_log_stdout = TEST_ROOT_DIR / "logs" / f"process_log_out-{uid}.txt"
            process_log_stderr = TEST_ROOT_DIR / "logs" / f"process_log_err-{uid}.txt"

            image_name = f"ghcr.io/ansys/pydpf-composites:{docker_image_tag}"

            return DockerProcess(
                server_out_file=server_log_stdout,
                server_err_file=server_log_stderr,
                process_out_file=process_log_stdout,
                process_err_file=process_log_stderr,
                license_server=get_license_server_string(license_server_config),
                image_name=image_name,
            )

    with start_server_process() as server_process:
        # Workaround for dpf bug. The timeout is not respected when connecting
        # to a server:https://github.com/ansys/pydpf-core/issues/638
        # We just try until connect_to_server succeeds
        def start_server():
            if server_process.port:
                return dpf.server.connect_to_server(port=server_process.port)
            else:
                return server_process.server

        server = _try_until_timeout(start_server, "Failed to start server.")

        _wait_until_server_is_up(server)
        server.apply_context(
            dpf.server.server_context.ServerContext(dpf.server_context.LicensingContextType.premium)
        )
        load_composites_plugin(server, ansys_path=installer_path)

        yield server


@pytest.fixture(params=[False, True])
def distributed_rst(request, dpf_server):
    """Fixture that parametrizes tests to run with a distributed RST or not."""
    res = request.param
    if res and not version_equal_or_later(dpf_server, "7.0"):
        pytest.skip(f"Distributed RST not supported for server version {dpf_server.version}.")
    return res
