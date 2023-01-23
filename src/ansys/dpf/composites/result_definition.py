"""Object to represent the Result Definition used by Failure Operator in DPF Composites."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, Optional, Sequence

from ._typing_helper import PATH as _PATH
from .failure_criteria.combined_failure_criterion import CombinedFailureCriterion
from .enums import FailureMeasure

_SUPPORTED_EXPRESSIONS = ["composite_failure"]
_SUPPORTED_MEASURES = [v.value for v in FailureMeasure]
_SUPPORTED_STRESS_STRAIN_EVAL_MODES = ["rst_file", "mapdl_live"]


@dataclass
class ResultDefinitionScope:
    """Result Definition Scope."""

    composite_definition: _PATH
    element_scope: Sequence[int] = field(default_factory=lambda: [])
    ply_scope: Sequence[str] = field(default_factory=lambda: [])
    """Assembly files which define the mapping of the labels
    This input is needed if multiple parts are assembled in WB / Mechanical to map the
    local element and node labels to the global ones.
    """
    mapping_file: Optional[_PATH] = None
    """Write the data for all element labels in element_scope.
    This makes sense if the user explicitly requests an element scope
    but the actual scope where postprocessing has happened is smaller
    (e.g. due to ply scoping).
    """
    write_data_for_full_element_scope: bool = True


class ResultDefinition:
    """Represents the result definition of DPF Composites.

    It is used to configure the DPF operators composite::failure_evaluator
    and composite::sampling_point_evaluator.
    """

    _VERSION = 1
    _ACCUMULATOR = "max"

    def __init__(
        self,
        name: str,
        combined_failure_criterion: CombinedFailureCriterion,
        composite_scopes: Sequence[ResultDefinitionScope],
        rst_file: _PATH,
        material_file: _PATH,
        measure: str = "inverse_reserve_factor",
        stress_strain_eval_mode: str = "rst_file",
        time: float = 1.0,
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
        self._rst_file = rst_file
        self._stress_strain_eval_mode = stress_strain_eval_mode
        # todo: is 1 a good default? Shouldn't it be last?
        self._time = time
        self._max_chunk_size = max_chunk_size

    @property
    def name(self) -> str:
        """Define a custom name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def expression(self) -> str:
        """Define the type of the result. Supported type is "composite_failure"."""
        return self._expression

    @expression.setter
    def expression(self, value: str) -> None:
        if value in _SUPPORTED_EXPRESSIONS:
            self._expression = value
        else:
            values = ", ".join([v for v in _SUPPORTED_EXPRESSIONS])
            raise ValueError(f"Expression {value} is not allowed. Supported are {values}")

    @property
    def combined_failure_criterion(self) -> CombinedFailureCriterion:
        """Configure of the failure criteria such as Max Stress, Puck and Wrinkling."""
        return self._combined_failure_criterion

    @combined_failure_criterion.setter
    def combined_failure_criterion(self, cfc: CombinedFailureCriterion) -> None:
        self._combined_failure_criterion = cfc

    @property
    def measure(self) -> str:
        """Define the return type of the failure values.

        Supported types are "inverse_reserve_factor", "safety_factor" and "safety_margin".
        """
        return self._measure

    @measure.setter
    def measure(self, value: str) -> None:
        if value not in _SUPPORTED_MEASURES:
            values = ", ".join([v for v in _SUPPORTED_MEASURES])
            raise ValueError(f"Measure {value} is not allowed. Supported are {values}")
        else:
            self._measure = value

    @property
    def scopes(self) -> Sequence[ResultDefinitionScope]:
        """Get the different scopes of the result definition."""
        return self._composite_scopes

    @scopes.setter
    def scopes(self, value: Sequence[ResultDefinitionScope]) -> None:
        self._composite_scopes = value

    @property
    def rst_file(self) -> _PATH:
        """Path of the result files (.rst)."""
        return self._rst_file

    @rst_file.setter
    def rst_file(self, value: _PATH) -> None:
        self._rst_file = value

    @property
    def material_file(self) -> _PATH:
        """Path of material files which store the material properties.

        Supported formats are XML and ENGD.
        """
        return self._material_file

    @material_file.setter
    def material_file(self, value: _PATH) -> None:
        self._material_file = value

    @property
    def stress_strain_eval_mode(self) -> str:
        """Results are loaded from a result file by default ("rst_file").

        Set to "mapdl_live" to activate on the fly strain and stress evaluation.
        Can be used if the result file contains only the primary results (deformations).
        """
        return self._stress_strain_eval_mode

    @stress_strain_eval_mode.setter
    def stress_strain_eval_mode(self, value: str) -> None:
        if value in _SUPPORTED_STRESS_STRAIN_EVAL_MODES:
            self._stress_strain_eval_mode = value
        else:
            values = ", ".join([v for v in _SUPPORTED_STRESS_STRAIN_EVAL_MODES])
            raise ValueError(
                f"Stress strain eval mode '{value} 'is not allowed. Supported are {values}"
            )

    @property
    def time(self) -> float:
        """Select time / solution step."""
        return self._time

    @time.setter
    def time(self, value: float) -> None:
        self._time = value

    @property
    def max_chunk_size(self) -> int:
        """Define the chunk size (number of elements) for the result evaluation.

        Small chunks reduces the maximum peak of memory but too many chunks causes
        some overhead. Default is 50'000. Use -1 to disable chunking.
        """
        return self._max_chunk_size

    @max_chunk_size.setter
    def max_chunk_size(self, value: int) -> None:
        self._max_chunk_size = value

    def to_dict(self) -> Dict[str, Any]:
        """Get the result definition in a dict representation."""
        cfc = self.combined_failure_criterion
        if not cfc:
            raise ValueError("Combined failure criterion is not defined!")

        if self.measure not in _SUPPORTED_MEASURES:
            values = ", ".join([v for v in _SUPPORTED_MEASURES])
            raise ValueError(f"Unknown measure `{self.measure}`. Supported are {values}")

        result_definition = {
            "version": self._VERSION,
            "accumulator": "max",
            "expression": f"{self.expression}",
            "failure_criteria_definition": {cfc.JSON_DICT_KEY: cfc.to_dict()},
            "measures": [self.measure],
            "stress_strain_eval_mode": f"{self.stress_strain_eval_mode}",
            "time": self.time,
            "max_chunk_size": self.max_chunk_size,
        }

        def get_scope(
            result_definition_scope: ResultDefinitionScope, rst_file: _PATH, material_file: _PATH
        ) -> Dict[str, Any]:
            write_for_full_scope = result_definition_scope.write_data_for_full_element_scope
            mapping_entry = []
            if result_definition_scope.mapping_file is not None:
                mapping_entry.append(str(result_definition_scope.mapping_file))
            return {
                "datasources": {
                    "composite_definition": [str(result_definition_scope.composite_definition)],
                    "assembly_mapping_file": mapping_entry,
                    "rst_file": [str(rst_file)],
                    "material_file": [str(material_file)],
                },
                "write_data_for_full_element_scope": write_for_full_scope,
                "elements": result_definition_scope.element_scope,
                "ply_ids": result_definition_scope.ply_scope,
            }

        scopes = {
            "scopes": [
                get_scope(scope, self.rst_file, self.material_file)
                for scope in self._composite_scopes
            ]
        }

        result_definition.update(scopes)
        return result_definition

    def to_json(self) -> str:
        """Convert the dict representation of the result definition into a JSON Dict."""
        return json.dumps(self.to_dict())

    def _get_properties(self, exclude: Sequence[str] = []) -> Sequence[Any]:
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
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """:return: string conversion."""
        s_attrs = ", ".join([f"{attr}={getattr(self, attr)}" for attr in self._get_properties()])
        s = f"{self.__class__.__name__}({s_attrs})"
        return s
