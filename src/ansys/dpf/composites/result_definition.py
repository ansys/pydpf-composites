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

"""Object to represent the result definition used by the failure operator in DPF Composites."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from ._typing_helper import PATH as _PATH
from .failure_criteria import CombinedFailureCriterion

__all__ = ("FailureMeasureEnum", "ResultDefinitionScope", "ResultDefinition")


class FailureMeasureEnum(str, Enum):
    """Provides available failure measures."""

    # TODO: Add descriptions for each property
    INVERSE_RESERVE_FACTOR = "inverse_reserve_factor"
    MARGIN_OF_SAFETY = "safety_margin"
    RESERVE_FACTOR = "safety_factor"


_SUPPORTED_EXPRESSIONS = ["composite_failure"]
_SUPPORTED_MEASURES = [v.value for v in FailureMeasureEnum]
_SUPPORTED_STRESS_STRAIN_EVAL_MODES = ["rst_file", "mapdl_live"]


@dataclass
class ResultDefinitionScope:
    """Provides the result definition scope."""

    composite_definition: _PATH
    element_scope: Sequence[int] = field(default_factory=lambda: [])
    ply_scope: Sequence[str] = field(default_factory=lambda: [])
    named_selection_scope: Sequence[str] = field(default_factory=lambda: [])
    """Assembly files that define the mapping of the labels.

    This attribute is needed if multiple parts are assembled in Workbench or
    Mechanical to map the local element and node labels to the global labels.
    """
    mapping_file: _PATH | None = None
    """Path to the mapping file for all element labels in the element scope.
    """

    write_data_for_full_element_scope: bool = True
    """Whether to write the data for all element labels in the element scope.

    This makes sense if an element scope is explicitly requested
    but the actual scope where postprocessing has happened is smaller,
    perhaps due to ply scoping.
    """


class ResultDefinition:
    """Represents the result definition of DPF Composites.

    This class is used to configure the DPF operators ``composite::failure_evaluator``
    and ``composite::sampling_point_evaluator``.

    """

    _VERSION = 1
    _ACCUMULATOR = "max"

    def __init__(
        self,
        name: str,
        combined_failure_criterion: CombinedFailureCriterion,
        composite_scopes: Sequence[ResultDefinitionScope],
        rst_files: Sequence[_PATH],
        material_file: _PATH,
        measure: str = "inverse_reserve_factor",
        stress_strain_eval_mode: str = "rst_file",
        time: float | None = None,
        expression: str = "composite_failure",
        max_chunk_size: int = 50000,
    ):
        """Create a ResultDefinition object."""
        self._name = name
        self._expression = expression
        self._combined_failure_criterion = combined_failure_criterion
        self._measure = measure
        self._composite_scopes = composite_scopes
        self._material_file = material_file
        self._rst_files = list(rst_files)
        self._stress_strain_eval_mode = stress_strain_eval_mode
        self._time = time
        self._max_chunk_size = max_chunk_size

    @property
    def name(self) -> str:
        """Custom name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def expression(self) -> str:
        """Type of the result. The supported type is ``"composite_failure"``."""
        return self._expression

    @expression.setter
    def expression(self, value: str) -> None:
        if value in _SUPPORTED_EXPRESSIONS:
            self._expression = value
        else:
            values = ", ".join([v for v in _SUPPORTED_EXPRESSIONS])
            raise ValueError(
                f"Expression {value} is not allowed. Supported expressions are {values}."
            )

    @property
    def combined_failure_criterion(self) -> CombinedFailureCriterion:
        """Configuration of the failure criteria such as maximum stress, puck, and wrinkling."""
        return self._combined_failure_criterion

    @combined_failure_criterion.setter
    def combined_failure_criterion(self, cfc: CombinedFailureCriterion) -> None:
        self._combined_failure_criterion = cfc

    @property
    def measure(self) -> str:
        """Return type of the failure values.

        Supported types are ``"inverse_reserve_factor"``, ``"safety_factor"``,
        and ``"safety_margin"``.
        """
        return self._measure

    @measure.setter
    def measure(self, value: str) -> None:
        if value not in _SUPPORTED_MEASURES:
            values = ", ".join([v for v in _SUPPORTED_MEASURES])
            raise ValueError(f"Measure {value} is not allowed. Supported measures are {values}.")
        else:
            self._measure = value

    @property
    def scopes(self) -> Sequence[ResultDefinitionScope]:
        """Scopes of the result definition."""
        return self._composite_scopes

    @scopes.setter
    def scopes(self, value: Sequence[ResultDefinitionScope]) -> None:
        self._composite_scopes = value

    @property
    def rst_files(self) -> list[_PATH]:
        """Path of the result (RST) files."""
        return self._rst_files

    @rst_files.setter
    def rst_files(self, value: list[_PATH]) -> None:
        self._rst_files = list(value)

    @property
    def material_file(self) -> _PATH:
        """Path of the material files that store the material properties.

        Supported formats are XML and ENGD.
        """
        return self._material_file

    @material_file.setter
    def material_file(self, value: _PATH) -> None:
        self._material_file = value

    @property
    def stress_strain_eval_mode(self) -> str:
        """Results loaded from a result (RST) file by default.

        You can set this property to ``"mapdl_live"`` to activate on-the-fly
        strain and stress evaluation. This property can be used if the result
        file contains only the primary results (deformations).
        """
        return self._stress_strain_eval_mode

    @stress_strain_eval_mode.setter
    def stress_strain_eval_mode(self, value: str) -> None:
        if value in _SUPPORTED_STRESS_STRAIN_EVAL_MODES:
            self._stress_strain_eval_mode = value
        else:
            values = ", ".join([v for v in _SUPPORTED_STRESS_STRAIN_EVAL_MODES])
            raise ValueError(
                f"Stress strain evaluation mode '{value}' is not allowed. "
                f"Supported values are {values}."
            )

    @property
    def time(self) -> float | None:
        """Time or solution step.

        DPF Composites automatically selects the last time step if time is not set.

        You can use the :meth:`.CompositeModel.get_result_times_or_frequencies` method
        to list the available times or frequencies in the result file.
        """
        return self._time

    @time.setter
    def time(self, value: float | None) -> None:
        self._time = value

    @property
    def max_chunk_size(self) -> int:
        """Maximum chunk size (number of elements) for the result evaluation.

        Small chunks reduce the maximum peak of memory, but too many chunks causes
        some overhead. The default is 50,000. Use ``-1`` to disable chunking.
        """
        return self._max_chunk_size

    @max_chunk_size.setter
    def max_chunk_size(self, value: int) -> None:
        self._max_chunk_size = value

    def to_dict(self) -> dict[str, Any]:
        """Get the result definition in a dictionary representation."""
        cfc = self.combined_failure_criterion
        if not cfc:
            raise ValueError("Combined failure criterion is not defined.")

        if self.measure not in _SUPPORTED_MEASURES:
            values = ", ".join([v for v in _SUPPORTED_MEASURES])
            raise ValueError(
                f"Measure `{self.measure}` is invalid. Supported measures are {values}."
            )

        result_definition = {
            "version": self._VERSION,
            "accumulator": "max",
            "expression": f"{self.expression}",
            "failure_criteria_definition": {cfc.JSON_DICT_KEY: cfc.to_dict()},
            "measures": [self.measure],
            "stress_strain_eval_mode": f"{self.stress_strain_eval_mode}",
            "max_chunk_size": self.max_chunk_size,
        }

        if self.time:
            result_definition["time"] = self.time

        def get_scope(
            result_definition_scope: ResultDefinitionScope,
            rst_files: list[_PATH],
            material_file: _PATH,
        ) -> dict[str, Any]:
            write_for_full_scope = result_definition_scope.write_data_for_full_element_scope
            mapping_entry = []
            if result_definition_scope.mapping_file is not None:
                mapping_entry.append(str(result_definition_scope.mapping_file))
            return {
                "datasources": {
                    "composite_definition": [str(result_definition_scope.composite_definition)],
                    "assembly_mapping_file": mapping_entry,
                    "rst_file": [str(filename) for filename in rst_files],
                    "material_file": [str(material_file)],
                },
                "write_data_for_full_element_scope": write_for_full_scope,
                "elements": [int(v) for v in result_definition_scope.element_scope],
                "ply_ids": result_definition_scope.ply_scope,
                "named_selections": result_definition_scope.named_selection_scope,
            }

        scopes = {
            "scopes": [
                get_scope(scope, self.rst_files, self.material_file)
                for scope in self._composite_scopes
            ]
        }

        result_definition.update(scopes)
        return result_definition

    def to_json(self) -> str:
        """Convert the dictionary representation of the result definition to a JSON dictionary."""
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

    def check_has_single_scope(self, msg: str) -> None:
        """Check that the result definition has one scope."""
        if len(self.scopes) != 1:
            raise RuntimeError(f"Result definition has multiple scopes. {msg}")

    def _short_descr(self) -> str:
        """:return: short description of the object."""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """:return: string conversion."""
        s_attrs = ", ".join([f"{attr}={getattr(self, attr)}" for attr in self._get_properties()])
        s = f"{self.__class__.__name__}({s_attrs})"
        return s
