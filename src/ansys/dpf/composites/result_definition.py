"""Object to represent the Result Definition used by Failure Operator in DPF Composites."""

import json
from typing import Any, Dict, Sequence, Type, Union

from ._typing_helper import PATH as _PATH
from .failure_criteria.combined_failure_criterion import CombinedFailureCriterion

# todo: is sampling point needed?
_SUPPORTED_EXPRESSIONS = ["composite_failure", "sampling_point"]
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
        expression: str = "composite_failure",
        combined_failure_criterion: Union[Type[CombinedFailureCriterion], None] = None,
        measures: Sequence[str] = ["inverse_reserve_factor"],
        composite_definitions: Sequence[_PATH] = [],
        assembly_mapping_files: Sequence[_PATH] = [],
        rst_files: Sequence[_PATH] = [],
        material_files: Sequence[_PATH] = [],
        write_data_for_full_element_scope: bool = True,
        element_scope: Sequence[int] = [],
        ply_scope: Sequence[str] = [],
        stress_strain_eval_mode: str = "rst_file",
        time: float = 1.0,
        max_chunk_size: int = 50000,
    ):
        """Create a ResultDefinition object."""
        self.name = name
        self.expression = expression
        self.combined_failure_criterion = combined_failure_criterion
        self.measures = measures
        self.composite_definitions = composite_definitions
        self.assembly_mapping_files = assembly_mapping_files
        self.rst_files = rst_files
        self.material_files = material_files
        self.write_data_for_full_element_scope = write_data_for_full_element_scope
        self.element_scope = element_scope
        self.ply_scope = ply_scope
        self.stress_strain_eval_mode = stress_strain_eval_mode
        # todo: is 1 a good default? Shouldn't it be last?
        self.time = time
        self.max_chunk_size = max_chunk_size

    def _get_expression(self) -> str:
        return self._expression

    def _set_expression(self, value: str) -> None:
        if value in _SUPPORTED_EXPRESSIONS:
            self._expression = value
        else:
            values = ", ".join([v for v in _SUPPORTED_EXPRESSIONS])
            raise ValueError(f"Expression {value} is not allowed. Supported are {values}")

    def _get_combined_failure_criterion(self) -> CombinedFailureCriterion:
        return self._combined_failure_criterion

    def _set_combined_failure_criterion(self, value: CombinedFailureCriterion) -> None:
        self._combined_failure_criterion = value

    def _get_measures(self) -> str:
        return self._meassures

    def _set_measures(self, value: str) -> None:
        for v in value:
            if v not in _SUPPORTED_MEASURES:
                values = ", ".join([v for v in _SUPPORTED_MEASURES])
                raise ValueError(f"Measure {value} is not allowed. Supported are {values}")
        else:
            self._meassures = value

    def _get_composite_definitions(self) -> Sequence[_PATH]:
        return self._composite_definitions

    def _set_composite_definitions(self, value: Sequence[_PATH]) -> None:
        if len(value) > 1:
            raise ValueError("Currently only 1 composite definition is supported!")
        self._composite_definitions = value

    def _get_assembly_mapping_files(self) -> Sequence[_PATH]:
        return self._assembly_mapping_files

    def _set_assembly_mapping_files(self, value: Sequence[_PATH]) -> None:
        self._assembly_mapping_files = value

    def _get_rst_files(self) -> Sequence[_PATH]:
        return self._rst_files

    def _set_rst_files(self, value: Sequence[_PATH]) -> None:
        self._rst_files = value

    def _get_material_files(self) -> Sequence[_PATH]:
        return self._material_files

    def _set_material_files(self, value: Sequence[_PATH]) -> None:
        self._material_files = value

    def _get_write_data_for_full_element_scope(self) -> bool:
        return self._write_data_for_full_element_scope

    def _set_write_data_for_full_element_scope(self, value: bool) -> None:
        self._write_data_for_full_element_scope = value

    def _get_element_scope(self) -> Sequence[int]:
        return self._element_scope

    def _set_element_scope(self, value: Sequence[int]) -> None:
        self._element_scope = value

    def _get_ply_scope(self) -> Sequence[str]:
        return self._ply_scope

    def _set_ply_scope(self, value: Sequence[str]) -> None:
        self._ply_scope = value

    def _get_stress_strain_eval_mode(self) -> str:
        return self._stress_strain_eval_mode

    def _set_stress_strain_eval_mode(self, value: str) -> None:
        if value in _SUPPORTED_STRESS_STRAIN_EVAL_MODES:
            self._stress_strain_eval_mode = value
        else:
            values = ", ".join([v for v in _SUPPORTED_STRESS_STRAIN_EVAL_MODES])
            raise ValueError(
                f"Stress strain eval mode '{value} 'is not allowed. Supported are {values}"
            )

    def _get_time(self) -> float:
        return self._time

    def _set_time(self, value: float) -> None:
        self._time = value

    def _get_max_chunk_size(self) -> int:
        return self._max_chunk_size

    def _set_max_chunk_size(self, value: int) -> None:
        self._max_chunk_size = value

    expression = property(
        _get_expression,
        _set_expression,
        doc="Defines the type of the computation. Supported are {0}".format(
            ", ".join([v for v in _SUPPORTED_EXPRESSIONS])
        ),
    )
    combined_failure_criterion = property(
        _get_combined_failure_criterion,
        _set_combined_failure_criterion,
        doc="Combined failure criterion with the selected failure criteria, failure modes and "
        "weighting factors",
    )
    measures = property(
        _get_measures,
        _set_measures,
        doc="Defines the type of failure measurement. Supported are {0}".format(
            ", ".join([v for v in _SUPPORTED_MEASURES])
        ),
    )
    composite_definitions = property(
        _get_composite_definitions,
        _set_composite_definitions,
        doc="List of ACP Composite Definitions (.h5) files which contain"
        " the lay-up information.",
    )
    assembly_mapping_files = property(
        _get_assembly_mapping_files,
        _set_assembly_mapping_files,
        doc="Optional: List of files (.h5) to map global node and element labels in an "
        "assembly. It is only used in the context of assemblies.",
    )
    rst_files = property(_get_rst_files, _set_rst_files, doc="List of result files (.rst).")
    material_files = property(
        _get_material_files,
        _set_material_files,
        doc="List of material files (.xml or .engd) " "which contain all material properties.",
    )
    write_data_for_full_element_scope = property(
        _get_write_data_for_full_element_scope,
        _set_write_data_for_full_element_scope,
        doc="If both an element and ply scope are defined, this option defines "
        "whether the results are computed on the intersection of the scopes "
        "or for all elements of the element scope. Elements which do not "
        "intersect with the ply scope will get the default value.",
    )
    element_scope = property(
        _get_element_scope,
        _set_element_scope,
        doc="List of element which are selected for the "
        "computation. All elements are selected"
        " if element_scope is an empty list.",
    )
    ply_scope = property(
        _get_ply_scope, _set_ply_scope, doc="List of plies which are selected for the computation."
    )
    # todo: describe what time means (load step, time, DPF time id, index)?
    time = property(_get_time, _set_time, doc="The results are computed for this time step.")
    max_chunk_size = property(
        _get_max_chunk_size,
        _set_max_chunk_size,
        doc="The computation is chunked. This parameter "
        "defines the number of elements per chunk.",
    )

    def to_dict(self) -> Dict[str, Any]:
        """:return: a dict with all properties."""
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
        """:return: the string representation (json.dumps).

        It can be used for the result definition of the DPF Composites Failure Operator.
        """
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


"""
const std::string example_result_definition = "{"
            "\"version\": 1,"
            // Currently unused, keep for max per layer etc.
            "\"accumulator\": \"max\","
            // Currently unused => remove
            "\"expression\": \"composite_failure\","
            "\"failure_criteria_definition\": {"
                "\"criteria\": {"
                    "\"max_stress\": {"
                        "\"active\": True,"
                        "\"s1\" : True,"
                        "\"s12\" : True,"
                        "\"s13\" : False,"
                        "\"s2\" : True,"
                        "\"s23\" : False,"
                        "\"s3\" : False,"
                        "\"wf_s1\" : 1,"
                        "\"wf_s12\" : 1,"
                        "\"wf_s13\" : 1,"
                        "\"wf_s2\" : 1,"
                        "\"wf_s23\" : 1,"
                        "\"wf_s3\" : 1"
                    "}"
                "}"
            "},"
            "\"measures\" : [\"inverse_reserve_factor\"],"
            "\"scopes\" : [{"
                "\"datasources\": {"
                    "\"composite_definition\": [\"example_path\"],"
                    "\"assembly_mapping_file\" : [] ,"
                    "\"rst_file\" : [\"example_path\"],"
                    "\"material_file\": [\"example_path\"]"
                "},"
                "\"write_data_for_full_element_scope\": false,"
                "\"elements\": [1, 2, 3, 4],"
                "\"ply_ids\": [\"ply1\"]"
            "}],"
            "\"stress_strain_eval_mode\": \"rst_file\","  // or mapdl_live
            "\"time\" : 1,"
            // Optional. Default is 50000
            "\"max_chunk_size\": 50000"
          "}";
"""
