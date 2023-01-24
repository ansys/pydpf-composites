from ansys.dpf.composites.failure_criteria._max_stress import ATTRS_MAX_STRESS, MaxStressCriterion

defaults = dict(
    zip(ATTRS_MAX_STRESS, [True, True, False, True, False, False, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
)


def test_max_stress_criterion():

    ms_default = MaxStressCriterion()
    assert ms_default.name == "Max Stress"

    defaults_dict = {"active": True}
    for v in ATTRS_MAX_STRESS:
        assert getattr(ms_default, v) == defaults[v]
        defaults_dict[v] = defaults[v]

    attr_values = ms_default.to_dict()
    for k, v in attr_values.items():
        assert v == defaults_dict[k]

    json_dumps = (
        '{"active": true, "s1": true, "s12": true, "s13": false, "s2": true, "s23": false, '
        '"s3": false, "wf_s1": 1.0, "wf_s12": 1.0, "wf_s13": 1.0, "wf_s2": 1.0, '
        '"wf_s23": 1.0, "wf_s3": 1.0}'
    )

    assert json_dumps == ms_default.to_json()

    new_values = dict(
        zip(ATTRS_MAX_STRESS, [False, False, True, False, True, True, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    )

    ms = MaxStressCriterion(**new_values)
    for v in ATTRS_MAX_STRESS:
        assert getattr(ms, v) == new_values[v]

    # test setters
    for k, v in new_values.items():
        setattr(ms_default, k, v)
        assert getattr(ms_default, k) == v

    # test repr
    ms.__repr__()
