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

"""Defines the base class of composite failure criterion."""

from collections.abc import Sequence
import json
from typing import Any


class FailureCriterionBase:
    """Defines the base class for failure criteria."""

    def __init__(self, *, name: str, active: bool):
        """Do not use directly! Construct a base failure criterion."""
        self.active = active
        self._name = name

    def _get_active(self) -> bool:
        return self._active

    def _set_active(self, value: bool) -> None:
        self._active = value

    def _get_name(self) -> str:
        return self._name

    active = property(
        _get_active, _set_active, doc="The failure criterion is suppressed if active is False."
    )
    name = property(_get_name, doc="Name of the failure criterion. Read only.")

    def to_dict(self) -> dict[str, Any]:
        """:return: a dict with all properties."""
        properties = self._get_properties(exclude=["name"])

        attr_dict = {}
        for prop in properties:
            attr_dict[prop] = getattr(self, prop)

        return attr_dict

    def to_json(self) -> str:
        """:return: the string representation of the object as JSON.

        It can be used for the result definition of the DPF Composites Failure Operator.
        """
        return json.dumps(self.to_dict())

    def _get_properties(self, exclude: Sequence[str] = tuple()) -> Sequence[Any]:
        properties = [
            attr
            for attr in dir(self)
            if not attr.startswith("__")
            and not attr.startswith("_")
            and not callable(getattr(self, attr))
            and attr not in exclude
        ]

        return properties

    def _short_descr(self) -> str:
        """:return: short description of the object."""
        return f"{self.__class__.__name__}(name='{self.name}', active={self.active})"

    def __repr__(self) -> str:
        """:return: string conversion."""
        s_attrs = ", ".join([f"{attr}={getattr(self, attr)}" for attr in self._get_properties()])
        s = f"{self.__class__.__name__}({s_attrs})"
        return s
