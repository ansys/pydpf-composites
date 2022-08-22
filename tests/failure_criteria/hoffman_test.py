import pytest

from ansys.dpf.composites.failure_criteria.hoffman import HoffmanCriterion

defaults = {"wf": 1., "dim": 2}
ATTRS = ["wf", "dim"]

def test_hoffman_criterion():

    hoffman_default = HoffmanCriterion()
    assert hoffman_default.name == "Hoffman"

    defaults_dict = {"active": True}
    for key in ATTRS:
        value = getattr(hoffman_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = hoffman_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = '{"active": true, "dim": 2, "wf": 1.0}'

    assert json_dumps == hoffman_default.to_json_dict()

    new_values = dict(zip(ATTRS, [2., 3]))

    hoffman = HoffmanCriterion(**new_values)
    for key in ATTRS:
        value = getattr(hoffman, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(hoffman_default, k, v)
        assert getattr(hoffman_default, k) == v

    # test repr
    print(hoffman)
