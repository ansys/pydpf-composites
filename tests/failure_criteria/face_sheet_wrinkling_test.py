from ansys.dpf.composites.failure_criteria.face_sheet_wrinkling import (
    ATTRS_WRINKLING,
    FaceSheetWrinklingCriterion,
)

defaults = dict(zip(ATTRS_WRINKLING, [0.5, 0.33, 1.0]))


def test_face_sheet_wrinkling_criterion():

    wrinkling_default = FaceSheetWrinklingCriterion()
    assert wrinkling_default.name == "Face Sheet Wrinkling"

    defaults_dict = {"active": True}
    for key in ATTRS_WRINKLING:
        value = getattr(wrinkling_default, key)
        assert value == defaults[key], f"{key}: {value} != {defaults[key]}"
        defaults_dict[key] = defaults[key]

    attr_values = wrinkling_default.to_dict()
    for key, value in attr_values.items():
        assert value == defaults_dict[key]

    json_dumps = (
        '{"active": true, "homogeneous_core_coeff": 0.5, "honeycomb_core_coeff": 0.33, "wf": 1.0}'
    )

    assert json_dumps == wrinkling_default.to_json()

    new_values = dict(zip(ATTRS_WRINKLING, [0.75, 0.53, 2.0]))

    wrinkling = FaceSheetWrinklingCriterion(**new_values)
    for key in ATTRS_WRINKLING:
        value = getattr(wrinkling, key)
        assert value == new_values[key], f"{key}: {value} != {new_values[key]}"

    # test setters
    for k, v in new_values.items():
        setattr(wrinkling_default, k, v)
        assert getattr(wrinkling_default, k) == v

    # test repr
    print(wrinkling)
