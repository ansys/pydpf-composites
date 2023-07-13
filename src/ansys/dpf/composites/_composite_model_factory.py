"""Composite Model Interface Factory."""
from typing import Callable, Optional, Union

from ansys.dpf.core import UnitSystem
from ansys.dpf.core.server_types import BaseServer

from ._composite_model_impl import CompositeModelImpl
from ._composite_model_impl_2023r2 import CompositeModelImpl2023R2
from .data_sources import ContinuousFiberCompositesFiles
from .server_helpers import version_older_than

CompositeModelImplT = Callable[
    [ContinuousFiberCompositesFiles, BaseServer, Optional[UnitSystem]],
    Union[CompositeModelImpl2023R2, CompositeModelImpl],
]


def _composite_model_factory(server: BaseServer) -> CompositeModelImplT:
    if version_older_than(server, "7.0"):
        return CompositeModelImpl2023R2

    return CompositeModelImpl
