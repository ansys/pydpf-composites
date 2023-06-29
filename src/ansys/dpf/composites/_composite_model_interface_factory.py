"""Composite Model Interface Factory."""
from typing import Callable, Optional, Union

from ansys.dpf.core import UnitSystem
from ansys.dpf.core.server_types import BaseServer

from ._composite_model_interface_2023r2 import CompositeModelInterface2023R2
from ._composite_model_interface_latest import CompositeModelInterface
from .data_sources import ContinuousFiberCompositesFiles
from .server_helpers import version_older_than

CompositeModelInterfaceT = Callable[
    [ContinuousFiberCompositesFiles, BaseServer, Optional[UnitSystem]],
    Union[CompositeModelInterface2023R2, CompositeModelInterface],
]


def _composite_model_interface_factory(server: BaseServer) -> CompositeModelInterfaceT:
    if version_older_than(server, "7.0"):
        return CompositeModelInterface2023R2

    return CompositeModelInterface2023R2  # CompositeModelInterface
