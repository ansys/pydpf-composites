import pytest

from ansys.dpf.composites.failure_criteria.shear_crimping import ShearCrimpingCriterion, ATTRS_SHEAR_CRIMPING

defaults = dict(zip(ATTRS_SHEAR_CRIMPING, [1., 0., 1.]))

def test_shear_crimping_criterion():

    sc_default = ShearCrimpingCriterion()
    assert sc_default.name == "Shear Crimping"

    defaults_dict = {"active": True}
    for key in ATTRS_SHEAR_CRIMPING:
        value = getattr(sc_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = sc_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = '{"active": true, "kc": 1.0, "kf": 0.0, "wf": 1.0}'

    assert json_dumps == sc_default.to_json()

    new_values = dict(zip(ATTRS_SHEAR_CRIMPING, [2., 1., 3.]))

    sc = ShearCrimpingCriterion(**new_values)
    for key in ATTRS_SHEAR_CRIMPING:
        value = getattr(sc, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(sc_default, k, v)
        assert getattr(sc_default, k) == v

    # test repr
    print(sc)
