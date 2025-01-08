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

"""Composite Scope."""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CompositeScope:
    """Provides the composite scope.

    This class defines which part of the model and solution step are selected.

    Parameters
    ----------
    elements:
        List of elements.
    plies:
        List of plies.
    time:
        Time or frequency. You can use the
        :meth:`.CompositeModel.get_result_times_or_frequencies` method
        to list the solution steps.
    named_selections:
        List of element sets.
        Use `composite_model.get_mesh().available_named_selections` to list
        all named selections.

    Notes
    -----
    If more than one scope (``elements``, ``named_selections`` and ``plies``)
    is set, then the final element scope is the intersection
    of the defined parameters. All elements are selected if no parameter is set.

    """

    elements: Sequence[int] | None = None
    plies: Sequence[str] | None = None
    time: float | None = None
    named_selections: Sequence[str] | None = None
