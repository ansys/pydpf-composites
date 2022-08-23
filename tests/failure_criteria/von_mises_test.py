from ansys.dpf.composites.failure_criteria.von_mises import ATTRS_VON_MISES, VonMisesCriterion

defaults = dict(zip(ATTRS_VON_MISES, [True, True, 1.0, 1.0, True, False]))


def test_von_mises_criterion():

    von_mises_default = VonMisesCriterion()
    assert von_mises_default.name == "Von Mises"

    defaults_dict = {"active": True}
    for key in ATTRS_VON_MISES:
        value = getattr(von_mises_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = von_mises_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "ins": false, "iss": true, "vme": true, "vms": true, '
        '"wf_vme": 1.0, "wf_vms": 1.0}'
    )

    assert json_dumps == von_mises_default.to_json()

    new_values = dict(zip(ATTRS_VON_MISES, [False, False, 2.0, 3.0, False, True]))

    von_mises = VonMisesCriterion(**new_values)
    for key in ATTRS_VON_MISES:
        value = getattr(von_mises, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(von_mises_default, k, v)
        assert getattr(von_mises_default, k) == v

    # test repr
    print(von_mises)
