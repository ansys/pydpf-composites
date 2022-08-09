"""
Defines the base class of composite failure criterion
"""

from typing import Any
import json

class FailureCriterionBase:

    def __init__(self,
                 name: str,
                 active: bool = True):
        self.active = active
        self._name = name

    def _get_active(self):
        return self._active
    def _set_active(self, value: bool = True):
        self._active = value

    def _get_name(self):
        return self._name

    active = property(_get_active, _set_active,
                      doc="Whether the failure criterion is active or not")
    name = property(_get_name, doc="Name of the failure criterion. Read only.")

    def to_json_dict(self) -> str:
        """
        :return: a json dict which can be used for the result definition of a dpf composite failure operator
        """
        attrs = [attr for attr in dir(self) if not attr.startswith('__')
                 and not attr.startswith('_')
                 and not attr.startswith('name')
                 and not callable(getattr(self, attr))]

        print(attrs)

        attr_dict = {}
        for attr in attrs:
            attr_dict[attr] = getattr(self, attr)

        key = self.name.lower().replace(" ", "_")
        failure_dict = {key: attr_dict}
        return json.dumps(failure_dict)

