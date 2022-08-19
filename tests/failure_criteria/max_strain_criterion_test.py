import json

from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion, ATTRS_MAX_STRAIN

defaults = dict(zip(ATTRS_MAX_STRAIN, [True, True, False, True, False, False, 1., 1., 1., 1., 1., 1.,
                                       False, 0., 0., 0., 0., 0., 0., 0., 0., 0.]))

def test_max_strain_criterion():

    ms_default = MaxStrainCriterion()
    assert ms_default.name == "Max Strain"

    defaults_dict = {"active": True}
    for v in ATTRS_MAX_STRAIN:
        assert getattr(ms_default, v) == defaults[v]
        defaults_dict[v] = defaults[v]

    attr_values = ms_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

    json_dumps = '{"active": true, "e12": 0.0, "e12_active": true, "e13": 0.0, "e13_active": false, ' \
                 '"e1_active": true, "e1c": 0.0, "e1t": 0.0, "e23": 0.0, "e23_active": false, ' \
                 '"e2_active": true, "e2c": 0.0, "e2t": 0.0, "e3_active": false, "e3c": 0.0, "e3t": 0.0, ' \
                 '"force_global_limits": false, ' \
                 '"wf_e1": 1.0, "wf_e12": 1.0, "wf_e13": 1.0, "wf_e2": 1.0, "wf_e23": 1.0, "wf_e3": 1.0}'

    assert json_dumps == ms_default.to_json_dict()

    new_values = dict(zip(ATTRS_MAX_STRAIN, [False, False, True, False, True, True, 2., 3., 4., 5., 6., 7.,
                                           True, 0.01, -0.1, 0.02, -0.2, 0.03, -0.3, 0.15, 0.25, 0.35]))

    ms = MaxStrainCriterion(**new_values)
    for v in ATTRS_MAX_STRAIN:
        assert getattr(ms, v) == new_values[v]

    # test setters
    for k, v in new_values.items():
        setattr(ms_default, k, v)
        assert getattr(ms_default, k) == v

    # test repr
    print(ms)