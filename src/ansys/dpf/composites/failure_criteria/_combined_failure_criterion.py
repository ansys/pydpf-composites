"""Combined Failure Criterion."""

import json
from typing import Any, Dict, Sequence

from ._failure_criterion_base import FailureCriterionBase


class CombinedFailureCriterion:
    """Defines the combined failure criterion.

    This class can be used in combination with the failure evaluator operator in
    DPF Composites.

    Examples
    --------
        >>> combined_failure = CombinedFailureCriterion("max_stress 3D")
        >>> max_stress = MaxStressCriterion(s1=True, s2=True, s3=True, s12=True, s13=True, s23=True)
        >>> combined_failure.insert(max_stress)

    """

    JSON_DICT_KEY = "criteria"

    def __init__(
        self,
        name: str = "CombinedFailureCriterion",
        failure_criteria: Sequence[FailureCriterionBase] = (),
    ):
        """Create a combined failure criterion.

        Parameters
        ----------
        name:
            User-defined name of the criterion.
        failure_criteria:
            List of failure criteria.
        """
        self._failure_criteria: Dict[str, FailureCriterionBase] = {}
        for fc in failure_criteria:
            self.insert(fc)

        self.name = name

    def _get_name(self) -> str:
        return self._name

    def _set_name(self, value: str) -> None:
        self._name = value

    def _get_failure_criteria(self) -> Dict[str, FailureCriterionBase]:
        return self._failure_criteria

    name = property(_get_name, _set_name, doc="Name of the combined failure criterion.")
    failure_criteria = property(
        _get_failure_criteria,
        doc="List of failure criteria. Use insert and remove to edit the list.",
    )

    def insert(self, fc: FailureCriterionBase) -> None:
        """Add a failure criterion to a list of selected criteria.

        Parameters
        ----------
        fc:
            Failure criterion to add. If a failure criterion of the same type
            already exists, it is overwritten.

        Examples
        --------
            >>> combined_failure = CombinedFailureCriterion("max_stress 3D")
            >>> max_stress = MaxStressCriterion(s1=True, s2=True, s3=True,
                                                s12=True, s13=True, s23=True)
            >>> combined_failure.insert(max_stress)

        """
        if fc is not None:
            self._failure_criteria[fc.name] = fc

    def remove(self, key: str) -> FailureCriterionBase:
        """Remove a failure criterion.

        Parameters
        ----------
        key:
            Name of the failure criterion.

        Returns
        -------
        :
            Removed failure criterion or ``None``.

        Examples
        --------
            >>> combined_failure.remove("Max Stress")

        """
        if not key in self._failure_criteria.keys():
            raise KeyError(f"{key} does not exist in the list of failure criteria.")

        return self._failure_criteria.pop(key)

    def to_dict(self) -> Dict[str, Any]:
        """Return the combined failure criterion as a dictionary.

        Returns
        -------
        :
            JSON dictionary that can be used for the result definition
            of the DPF Composites Failure evaluator operator.
        """
        criteria = {}
        for _, fc in self.failure_criteria.items():
            # returns a dict of all attributes
            attr_dict = fc.to_dict()
            # get the name and use it as key to add the attrs
            key = fc.name.lower().replace(" ", "_")
            failure_dict = {key: attr_dict}
            criteria.update(failure_dict)

        return criteria

    def to_json(self) -> str:
        """Return the combined failure criterion as a JSON dictionary.

        Returns
        -------
        :
           String representation (``json.dumps`` file) that can be used for the result definition
           of the DPF Composites Failure evaluator operator.
        """
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        """Return a description of the combined failure criteria."""
        s_criteria = ", ".join(
            [f"'{k}': {fc._short_descr()}" for k, fc in self.failure_criteria.items()]
        )
        s = f"{self.__class__.__name__}(failure_criteria={{{s_criteria}}})"
        return s
