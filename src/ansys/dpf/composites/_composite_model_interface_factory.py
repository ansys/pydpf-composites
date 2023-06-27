"""Composite Model Interface Factory."""
from packaging import version
from typing import Union

from ansys.dpf.core.server_types import BaseServer

from ._composite_model_interface_2023r2 import CompositeModelInterface2023R2


def _composite_model_interface_factory(server: BaseServer) -> Union[CompositeModelInterface2023R2]:
    dpf_server_version = version.parse(server.version)
    if dpf_server_version < version.parse("7.0"):
        return CompositeModelInterface2023R2

    return CompositeModelInterface2023R2


