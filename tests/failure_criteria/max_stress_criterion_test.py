import json

from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion, ATTRS_MAX_STRESS

defaults = [True, True, False, True, False, False, 1., 1., 1., 1., 1., 1.]

def test_max_stress_criterion():

    max_stress_default = MaxStressCriterion()
    defaults_dict = {"active": True}
    for i, v in enumerate(ATTRS_MAX_STRESS):
        assert getattr(max_stress_default, v) == defaults[i]
        defaults_dict[v] = defaults[i]

    attr_values = max_stress_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

