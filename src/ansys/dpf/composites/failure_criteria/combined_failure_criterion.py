"""Combined Failure Criterion."""

import json
from typing import Any, Sequence


class CombinedFailureCriterion:
    """

    Defines the Combined Failure Criterion that can be used in combination with
    Failure Evaluator operator in DPF Composites.

    Usage:
        combined_failure = CombinedFailureCriterion("max_stress 3D")
        max_stress = MaxStressCriterion(s1=True, s2=True, s3=True,
            s12=True, s13=True, s23=True)
        combined_failure.insert(max_stress)

    """

    JSON_DICT_KEY = "criteria"

    def __init__(
        self, name: str = "CombinedFailureCriterion", failure_criteria: Sequence[Any] = []
    ):
        """

        Create a new combined failure criterion.

        :param name: user-defined name of the criterion
        :param failure_criteria: list of failure criteria
        """
        self._failure_criteria = {}
        for fc in failure_criteria:
            self.insert(fc)

        self.name = name

    def _get_name(self) -> str:
        return self._name

    def _set_name(self, value: str):
        self._name = value

    def _get_failure_criteria(self):
        return self._failure_criteria

    name = property(_get_name, _set_name, doc="Name of the combined failure criterion.")
    failure_criteria = property(
        _get_failure_criteria, doc="List of failure criteria. Use insert and remove to edit it."
    )

    def insert(self, fc=None):
        """

        :param fc: Adds a failure criterion to list of selected criteria. Overwrites an entity if a
        failure criterion of the same type already exists.

        Example:
            combined_failure = CombinedFailureCriterion("max_stress 3D")
            max_stress = MaxStressCriterion(s1=True, s2=True, s3=True,
                 s12=True, s13=True, s23=True)
            combined_failure.insert(max_stress)

        """

        if fc is not None:
            self._failure_criteria[fc.name] = fc

    def remove(self, key):
        """

        Removes a failure criterion from the list
        :param key: Name of the failure criterion
        :return: the removed failure criterion or None

        Example:
            combined_failure.remove("Max Stress")

        """

        if key in self._failure_criteria.keys():
            return self._failure_criteria.pop(key)
        return None

    def to_dict(self) -> dict:
        """

        :return: the json_dict which can be used for the result definition
        of the DPF Composites Failure Operator

        """

        criteria = {}
        for k, fc in self.failure_criteria.items():
            # returns a dict of all attributes
            attr_dict = fc.to_dict()
            # get the name and use it as key to add the attrs
            key = fc.name.lower().replace(" ", "_")
            failure_dict = {key: attr_dict}
            criteria.update(failure_dict)

        return criteria

    def to_json(self) -> str:
        """

        :return: the string representation (json.dumps) which can be used for the result definition
        of the DPF Composites Failure Operator
        """

        return json.dumps(self.to_dict())

    def __repr__(self):
        s_criteria = ", ".join(
            [f"'{k}': {fc._short_descr()}" for k, fc in self.failure_criteria.items()]
        )
        s = f"{self.__class__.__name__}(failure_criteria={{{s_criteria}}})"
        return s
