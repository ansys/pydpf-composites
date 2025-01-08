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

"""Composite Model Interface Factory."""
from collections.abc import Callable
from typing import Optional, Union

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
