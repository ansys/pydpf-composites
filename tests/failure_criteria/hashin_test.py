from ansys.dpf.composites.failure_criteria._hashin import ATTRS_HASHIN, HashinCriterion

defaults = dict(zip(ATTRS_HASHIN, [True, True, False, 2, 1.0, 1.0, 1]))


def test_hashin_criterion():
    hashin_default = HashinCriterion()
    assert hashin_default.name == "Hashin"

    defaults_dict = {"active": True}
    for key in ATTRS_HASHIN:
        value = getattr(hashin_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = hashin_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "dim": 2, "hd": false, "hf": true, "hm": true, "wf_hd": 1.0, '
        '"wf_hf": 1.0, "wf_hm": 1.0}'
    )

    assert json_dumps == hashin_default.to_json()

    new_values = dict(zip(ATTRS_HASHIN, [False, False, True, 3, 2.0, 4.0, 5.0]))

    hashin = HashinCriterion(**new_values)
    for key in ATTRS_HASHIN:
        value = getattr(hashin, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(hashin_default, k, v)
        assert getattr(hashin_default, k) == v

    # test repr
    hashin.__repr__()
