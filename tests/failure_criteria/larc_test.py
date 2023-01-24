from ansys.dpf.composites.failure_criteria._larc import ATTRS_LARC, LaRCCriterion

defaults = dict(zip(ATTRS_LARC, [True, True, True, True, 2, 1.0, 1.0, 1.0, 1.0]))


def test_larc_criterion():

    larc_default = LaRCCriterion()
    assert larc_default.name == "LaRC"

    defaults_dict = {"active": True}
    for key in ATTRS_LARC:
        value = getattr(larc_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = larc_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "dim": 2, "lfc": true, "lft": true, "lmc": true, "lmt": true, '
        '"wf_lfc": 1.0, "wf_lft": 1.0, "wf_lmc": 1.0, "wf_lmt": 1.0}'
    )

    assert json_dumps == larc_default.to_json()

    new_values = dict(zip(ATTRS_LARC, [False, False, False, False, 3, 2.0, 4.0, 5.0, 6.0]))

    larc = LaRCCriterion(**new_values)
    for key in ATTRS_LARC:
        value = getattr(larc, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(larc_default, k, v)
        assert getattr(larc_default, k) == v

    # test repr
    larc.__repr__()
