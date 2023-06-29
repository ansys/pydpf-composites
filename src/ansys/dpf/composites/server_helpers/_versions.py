import dataclasses
from typing import Dict

from ansys.dpf.core.server_types import BaseServer
from packaging import version


@dataclasses.dataclass(frozen=True)
class _DpfVersionInfo:
    server_version: str
    wb_version: str
    description: str


_DPF_VERSIONS: Dict[str, _DpfVersionInfo] = {
    "5.0": _DpfVersionInfo("5.0", "2023 R1", "Initial release of DPF Composites."),
    "7.0": _DpfVersionInfo("7.0", "2024 R1", "DPF Composites plugin with sub-operators."),
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
