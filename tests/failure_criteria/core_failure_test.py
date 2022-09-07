from ansys.dpf.composites.failure_criteria.core_failure import (
    ATTRS_CORE_FAILURE,
    CoreFailureCriterion,
)

defaults = dict(zip(ATTRS_CORE_FAILURE, [False, 1.0]))


def test_core_failure_criterion():

    cf_default = CoreFailureCriterion()
    assert cf_default.name == "Core Failure"

    defaults_dict = {"active": True}
    for v in ATTRS_CORE_FAILURE:
        assert getattr(cf_default, v) == defaults[v]
        defaults_dict[v] = defaults[v]

    attr_values = cf_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

    json_dumps = '{"active": true, "include_ins": false, "wf": 1.0}'

    assert json_dumps == cf_default.to_json()

    new_values = dict(zip(ATTRS_CORE_FAILURE, [True, 2.0]))

    cf = CoreFailureCriterion(**new_values)
    for v in ATTRS_CORE_FAILURE:
        assert getattr(cf, v) == new_values[v]

    # test setters
    for k, v in new_values.items():
        setattr(cf_default, k, v)
        assert getattr(cf_default, k) == v

    # test repr
    cf.__repr__()
