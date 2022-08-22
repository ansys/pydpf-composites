import pytest

from ansys.dpf.composites.failure_criteria.cuntze import CuntzeCriterion, ATTRS_CUNTZE

defaults = dict(zip(ATTRS_CUNTZE, [True, True, True, True, True, 2, 1., 1., 1., 1., 1., 0.2,
                                   1.3805, 53., 2.6]))

def test_cuntze_criterion():

    cuntze_default = CuntzeCriterion()
    assert cuntze_default.name == "Cuntze"

    defaults_dict = {"active": True}
    for key in ATTRS_CUNTZE:
        value = getattr(cuntze_default, key)
        if key in ["b32", "fracture_plane_angle"]:
            assert abs(value - defaults[key]) < 1.e-4, f"{key}: {value} != {defaults[key]}"
        else:
            assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = cuntze_default.to_dict()
    for key, value in attr_values.items():
        if key in ["b32", "fracture_plane_angle"]:
            assert abs(value - defaults[key]) < 1.e-4, f"{key}: {value} != {defaults[key]}"
        else:
            assert value == defaults_dict[key]

    json_dumps = '{"active": true, "b21": 0.2, "b32": 1.3805239792947728, "cfc": true, "cft": true, "cma": true, ' \
                 '"cmb": true, "cmc": true, "dim": 2, "fracture_plane_angle": 53.0, "mode_interaction_coeff": 2.6, ' \
                 '"wf_cfc": 1.0, "wf_cft": 1.0, "wf_cma": 1.0, "wf_cmb": 1.0, "wf_cmc": 1.0}'

    assert json_dumps == cuntze_default.to_json_dict()

    new_values = dict(zip(ATTRS_CUNTZE, [False, False, False, False, False,
                                         3, 2., 4., 5., 6., 7., 0.4, 2., 60., 3.]))

    cuntze = CuntzeCriterion(**new_values)
    for key in ATTRS_CUNTZE:
        value = getattr(cuntze, key)
        if key in ["b32", "fracture_plane_angle"]:
            assert abs(value - new_values[key]) < 1.e-4, f"{key}: {value} != {new_values[key]}"
        else:
            assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(cuntze_default, k, v)
        assert getattr(cuntze_default, k) == v

    # test repr
    print(cuntze)
