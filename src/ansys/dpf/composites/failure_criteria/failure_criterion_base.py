"""Defines the base class of composite failure criterion"""

import json


class FailureCriterionBase:
    def __init__(self, name: str, active: bool):
        self.active = active
        self._name = name

    def _get_active(self) -> bool:
        return self._active

    def _set_active(self, value: bool):
        self._active = value

    def _get_name(self) -> str:
        return self._name

    active = property(
        _get_active, _set_active, doc="The failure criterion is suppressed if active is False."
    )
    name = property(_get_name, doc="Name of the failure criterion. Read only.")

    def to_dict(self) -> dict:
        """
        :return: a dict with all properties
        """
        properties = self._get_properties(exclude=["name"])

        attr_dict = {}
        for prop in properties:
            attr_dict[prop] = getattr(self, prop)

        return attr_dict

    def to_json(self):
        """
        :return: the string representation of the dict (json.dumps) which can be used for
        the result definition of the DPF Composites Failure Operator
        """
        return json.dumps(self.to_dict())

    def _get_properties(self, exclude=[]):
        properties = [
            attr
            for attr in dir(self)
            if not attr.startswith("__")
            and not attr.startswith("_")
            and not callable(getattr(self, attr))
            and attr not in exclude
        ]

        return properties

    def _short_descr(self):
        return f"{self.__class__.__name__}(name='{self.name}', active={self.active})"

    def __repr__(self):
        s_attrs = ", ".join([f"{attr}={getattr(self, attr)}" for attr in self._get_properties()])
        s = f"{self.__class__.__name__}({s_attrs})"
        return s
