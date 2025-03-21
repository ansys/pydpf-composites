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

import dataclasses

from ansys.dpf.core.server_types import BaseServer
from packaging import version


@dataclasses.dataclass(frozen=True)
class _DpfVersionInfo:
    server_version: str
    wb_version: str
    description: str


_DPF_VERSIONS: dict[str, _DpfVersionInfo] = {
    "5.0": _DpfVersionInfo("5.0", "2023 R1", "Initial release of DPF Composites."),
    "7.0": _DpfVersionInfo("7.0", "2024 R1 pre 0", "DPF Composites plugin with sub-operators."),
    "7.1": _DpfVersionInfo(
        "7.1", "2024 R1", "DPF Composites: layer index starts at 1. Material names."
    ),
    "8.0": _DpfVersionInfo(
        "8.0",
        "2024 R2 pre 0",
        "DPF Composites: reference surface support and \
                                                   section data from RST",
    ),
    "8.2": _DpfVersionInfo(
        "8.2",
        "2024 R2 pre 2",
        "DPF Composites: Failure measure conversion preserves Reference Surface suffix",
    ),
    "9.0": _DpfVersionInfo(
        "9.0",
        "2025 R1 pre 0",
        "DPF Composites: exposure of ply type and support of imported solid models.",
    ),
    "10.0": _DpfVersionInfo(
        "10.0",
        "2025 R2",
        "DPF Composites: basic support of LSDyna and sampling points for solids.",
    ),
}


def _check_key(ver: str) -> None:
    if ver not in _DPF_VERSIONS.keys():
        msg = ", ".join([f"{index}:{ver.server_version}" for index, ver in _DPF_VERSIONS.items()])
        raise RuntimeError(f"Invalid key `{ver}`. Allowed values are {msg}.")


def version_older_than(server: BaseServer, ver: str) -> bool:
    """Evaluate if the dpf server is older than the given version."""
    _check_key(ver)
    version_info = _DPF_VERSIONS[ver]
    return version.parse(server.version) < version.parse(version_info.server_version)


def version_equal_or_later(server: BaseServer, ver: str) -> bool:
    """Evaluate if the dpf server is equal or newer than the given version."""
    _check_key(ver)
    version_info = _DPF_VERSIONS[ver]
    return version.parse(server.version) >= version.parse(version_info.server_version)
