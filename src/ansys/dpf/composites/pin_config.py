"""Pin config helper."""


def get_pin_config():
    """Temporary helper for pin numbers.

    :return:
    dict with pinnumbers
    """
    return {
        "input": {
            "data_source": 4,
            "property": 13,
            "mesh_region": 7,
            "configuration": 100,
            "strains": 0,
            "stresses": 1,
            "materials_container": 23,
            "material_support": 21,
        },
        "output": {
            "min": 0,
            "max": 1,
            "mode_index": 0,
            "value_index": 1,
        },
    }
