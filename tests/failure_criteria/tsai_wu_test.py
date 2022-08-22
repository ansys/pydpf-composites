import pytest

from ansys.dpf.composites.failure_criteria.tsai_wu import TsaiWuCriterion

defaults = {"wf": 1., "dim": 2}
ATTRS = ["wf", "dim"]

def test_tsai_wu_criterion():

    tw_default = TsaiWuCriterion()
    assert tw_default.name == "Tsai Wu"

    defaults_dict = {"active": True}
    for key in ATTRS:
        value = getattr(tw_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = tw_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = '{"active": true, "dim": 2, "wf": 1.0}'

    assert json_dumps == tw_default.to_json_dict()

    new_values = dict(zip(ATTRS, [2., 3]))

    tsai_wu = TsaiWuCriterion(**new_values)
    for key in ATTRS:
        value = getattr(tsai_wu, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(tw_default, k, v)
        assert getattr(tw_default, k) == v

    # test repr
    print(tsai_wu)
