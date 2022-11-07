"""Object to represent the Result Definition used by Failure Operator in DPF Composites."""

import json
from typing import Any, Dict, Sequence

from ._typing_helper import PATH as _PATH
from .failure_criteria.combined_failure_criterion import CombinedFailureCriterion

_SUPPORTED_EXPRESSIONS = ["composite_failure"]
_SUPPORTED_MEASURES = ["inverse_reserve_factor", "safety_factor", "safety_margin"]
_SUPPORTED_STRESS_STRAIN_EVAL_MODES = ["rst_file", "mapdl_live"]


class ResultDefinition:
    """Represent the result definition used in DPF Composites.

    It can be used in combination with the composite::failure_evaluator and
    composite::sampling_point_evaluator, and others.
    """

    _VERSION = 1
    _ACCUMULATOR = "max"

    # todo: TBD: measures, composite_definitions, material_files are list
    # where we just support one file.
    # should this class work with lists or just single entries?
    def __init__(
        self,
        name: str,
        combined_failure_criterion: CombinedFailureCriterion,
        composite_definitions: Sequence[_PATH],
        rst_files: Sequence[_PATH],
        material_files: Sequence[_PATH],
        assembly_mapping_files: Sequence[_PATH] = [],
        measures: Sequence[str] = ["inverse_reserve_factor"],
        write_data_for_full_element_scope: bool = True,
        element_scope: Sequence[int] = [],
        ply_scope: Sequence[str] = [],
        stress_strain_eval_mode: str = "rst_file",
        time: float = 1.0,
        expression: str = "composite_failure",
        max_chunk_size: int = 50000,
    ):
        """Create a ResultDefinition object."""
        self._name = name
        self._expression = expression
        self._combined_failure_criterion = combined_failure_criterion
        self._measures = measures
        self._composite_definitions = composite_definitions
        self._assembly_mapping_files = assembly_mapping_files
        self._rst_files = rst_files
        self._material_files = material_files
        self._write_data_for_full_element_scope = write_data_for_full_element_scope
        self._element_scope = element_scope
        self._ply_scope = ply_scope
        self._stress_strain_eval_mode = stress_strain_eval_mode
        # todo: is 1 a good default? Shouldn't it be last?
        self._time = time
        self._max_chunk_size = max_chunk_size

    @property
    def expression(self):
        """Defines the type of the result. Supported type is "composite_failure" """
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
        """Configuration of the failure criteria such as Max Stress, Puck and Wrinkling."""
        return self._combined_failure_criterion


    @property
    def measures(self) -> str:
        """Defines the return type of the failure values.
        
        Supported types are "inverse_reserve_factor", "safety_factor" and "safety_margin"."""
        return self._meassures

    @measures.setter
    def measures(self, value: str) -> None:
        for v in value:
            if v not in _SUPPORTED_MEASURES:
                values = ", ".join([v for v in _SUPPORTED_MEASURES])
                raise ValueError(f"Measure {value} is not allowed. Supported are {values}")
        else:
            self._meassures = value

    @property
    def composite_definitions(self) -> Sequence[_PATH]:
        """File path of the composite definitions file of ACP.

        This file includes the section data such as ply material, angle and thickness."""
        return self._composite_definitions

    @composite_definitions.setter
    def composite_definitions(self, value: Sequence[_PATH]) -> None:
        if len(value) > 1:
            raise ValueError("Currently only 1 composite definition is supported!")
        self._composite_definitions = value

    @property
    def assembly_mapping_files(self) -> Sequence[_PATH]:
        """Assembly files which define the mapping of the labels (optional).

        This input is needed if multiple parts are assembled in WB / Mechanical to map the
        local element and node labels to the global ones."""
        return self._assembly_mapping_files

    @assembly_mapping_files.setter
    def assembly_mapping_files(self, value: Sequence[_PATH]) -> None:
        self._assembly_mapping_files = value

    @property
    def rst_files(self) -> Sequence[_PATH]:
        """Path of the result files (.rst)"""
        return self._rst_files

    @rst_files.setter
    def rst_files(self, value: Sequence[_PATH]) -> None:
        self._rst_files = value

    @property
    def material_files(self) -> Sequence[_PATH]:
        """Path of material files which store the material properties.

        Supported formats are XML and ENGD."""
        return self._material_files

    @material_files.setter
    def material_files(self, value: Sequence[_PATH]) -> None:
        self._material_files = value

    @property
    def write_data_for_full_element_scope(self) -> bool:
        """Write the data for all element labels in element_scoping.

        This makes sense if the user explicitly requests an element scope
        but the actual scope where postprocessing has happened is smaller
        (e.g. due to ply scoping).
        """
        return self._write_data_for_full_element_scope

    @write_data_for_full_element_scope.setter
    def write_data_for_full_element_scope(self, value: bool) -> None:
        self._write_data_for_full_element_scope = value

    @property
    def element_scope(self) -> Sequence[int]:
        """Define the scope through a list of element labels.

        All elements are selected if element_scope is an empty list."""
        return self._element_scope

    @element_scope.setter
    def element_scope(self, value: Sequence[int]) -> None:
        self._element_scope = value

    @property
    def ply_scope(self) -> Sequence[str]:
        """List of plies for ply-wise post-processing (optional).

        Is used in combination with element_scope."""
        return self._ply_scope

    @ply_scope.setter
    def ply_scope(self, value: Sequence[str]) -> None:
        self._ply_scope = value

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

        result_definition = {
            "version": self._VERSION,
            "accumulator": "max",
            "expression": f"{self.expression}",
            "failure_criteria_definition": {cfc.JSON_DICT_KEY: cfc.to_dict()},
            "measures": self.measures,
            "stress_strain_eval_mode": f"{self.stress_strain_eval_mode}",
            "time": self.time,
            "max_chunk_size": self.max_chunk_size,
        }

        scopes = {
            "scopes": [
                {
                    "datasources": {
                        "composite_definition": self.composite_definitions,
                        "assembly_mapping_file": self.assembly_mapping_files,
                        "rst_file": self.rst_files,
                        "material_file": self.material_files,
                    },
                    "write_data_for_full_element_scope": self.write_data_for_full_element_scope,
                    "elements": self.element_scope,
                    "ply_ids": self.ply_scope,
                }
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
