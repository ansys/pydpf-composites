from ansys.dpf.composites.failure_criteria.tsai_hill import TsaiHillCriterion

defaults = {"wf": 1.0, "dim": 2}
ATTRS = ["wf", "dim"]


def test_tsai_hill_criterion():

    th_default = TsaiHillCriterion()
    assert th_default.name == "Tsai Hill"

    defaults_dict = {"active": True}
    for key in ATTRS:
        value = getattr(th_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = th_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = '{"active": true, "dim": 2, "wf": 1.0}'

    assert json_dumps == th_default.to_json()

    new_values = dict(zip(ATTRS, [2.0, 3]))

    tsai_hill = TsaiHillCriterion(**new_values)
    for key in ATTRS:
        value = getattr(tsai_hill, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(th_default, k, v)
        assert getattr(th_default, k) == v

    # test repr
    print(tsai_hill)
