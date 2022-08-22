"""Failure config helper."""

from typing import Any, Dict


def get_failure_criteria_definition() -> Dict[str, Any]:
    """Return dummy failure configuration.

    :return:
     dict with dummy failure config
    """
    max_strain_json_configuration = {
        "active": True,
        "e1": True,
        "e12": True,
        "e13": False,
        "e2": True,
        "e23": False,
        "e3": False,
        "eSxy": 0.015,
        "eSxz": 0.015,
        "eSyz": 0.015,
        "eXc": -0.008,
        "eXt": 0.01,
        "eYc": -0.008,
        "eYt": 0.01,
        "eZc": -0.008,
        "eZt": 0.01,
        "force_global_strain_limits": False,
        "wf_e1": 1,
        "wf_e12": 1,
        "wf_e13": 1,
        "wf_e2": 1,
        "wf_e23": 1,
        "wf_e3": 1,
    }
    max_stress_json_configuration_2d = {
        "active": True,
        "s1": True,
        "s12": True,
        "s13": False,
        "s2": True,
        "s23": False,
        "s3": False,
        "wf_s1": 1,
        "wf_s12": 1,
        "wf_s13": 1,
        "wf_s2": 1,
        "wf_s23": 1,
        "wf_s3": 1,
    }
    quadratic_failure_json_configuration_2d = {"active": True, "dim": 2, "wf": 1}
    hashin_json_configuration = {
        "active": True,
        "dim": 2,
        "hd": True,
        "hf": True,
        "hm": True,
        "wf_hd": 1.0,
        "wf_hf": 1.0,
        "wf_hm": 1.0,
    }
    cuntze_failure_json_configuration = {
        "active": True,
        "b21": 0.2,
        "b32": 1.38,
        "cfc": True,
        "cft": True,
        "cma": True,
        "cmb": True,
        "cmc": True,
        "dim": 2,
        "fracture_plane_angle": 53,
        "mode_interaction_coeff": 2.6,
        "wf_cfc": 1,
        "wf_cft": 1,
        "wf_cma": 1,
        "wf_cmb": 1,
        "wf_cmc": 1,
    }

    core_failure_json_configuration = {"active": True, "include_ins": False, "wf": 1}

    von_mises_only_strain_json_configuration = {
        "active": True,
        "vme": True,
        "vms": False,
        "wf_vme": 1.0,
        "wf_vms": 1.0,
    }

    return {
        "max_strain": max_strain_json_configuration,
        "max_stress": max_stress_json_configuration_2d,
        "hashin": hashin_json_configuration,
        "tsai_hill": quadratic_failure_json_configuration_2d,
        "tsai_wu": quadratic_failure_json_configuration_2d,
        "hoffman": quadratic_failure_json_configuration_2d,
        "core_failure": core_failure_json_configuration,
        "von_mises": von_mises_only_strain_json_configuration,
        "cuntze": cuntze_failure_json_configuration,
    }
