# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""Collection of constants used across PyDPF Composites."""
from enum import IntEnum

__all__ = (
    "Spot",
    "Sym3x3TensorComponent",
    "FailureOutput",
    "REF_SURFACE_NAME",
    "FAILURE_LABEL",
    "TIME_LABEL",
)

FAILURE_LABEL = "failure_label"
TIME_LABEL = "time"


class Spot(IntEnum):
    """Implements an interface to access the spots of the results of layered elements."""

    BOTTOM = 1
    MIDDLE = 2
    TOP = 3


class Sym3x3TensorComponent(IntEnum):
    """Provides tensor indices for symmetrical 3x3 tensors."""

    TENSOR11 = 0
    TENSOR22 = 1
    TENSOR33 = 2
    TENSOR21 = 3
    TENSOR31 = 5
    TENSOR32 = 4


class FailureOutput(IntEnum):
    """Provides failure output types.

    The enum value corresponds to the index in the fields container.
    """

    FAILURE_MODE = 0
    FAILURE_VALUE = 1
    MAX_LAYER_INDEX = 2
    FAILURE_MODE_REF_SURFACE = 3
    FAILURE_VALUE_REF_SURFACE = 4
    MAX_GLOBAL_LAYER_IN_STACK = 5
    MAX_LOCAL_LAYER_IN_ELEMENT = 6
    MAX_SOLID_ELEMENT_ID = 7


REF_SURFACE_NAME = "Reference Surface"
