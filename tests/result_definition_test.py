from typing import Any, Dict

from ansys.dpf.composites.failure_criteria._combined_failure_criterion import (
    CombinedFailureCriterion,
)
from ansys.dpf.composites.failure_criteria._max_strain import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria._max_stress import MaxStressCriterion
from ansys.dpf.composites.result_definition import (
    _SUPPORTED_EXPRESSIONS,
    _SUPPORTED_MEASURES,
    ResultDefinition,
    ResultDefinitionScope,
)

defaults: Dict[str, Any] = {
    "expression": "composite_failure",
    "measure": "inverse_reserve_factor",
    "stress_strain_eval_mode": "rst_file",
    "time": 1.0,
    "max_chunk_size": 50000,
}


def test_result_definition():
    cfc = CombinedFailureCriterion("max strain & max stress")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())

    scope = ResultDefinitionScope(
        composite_definition=r"\\workdir\ACPCompositeDefinitions.h5",
    )

    rd = ResultDefinition(
        name="my first result definition",
        combined_failure_criterion=cfc,
        composite_scopes=[scope],
        rst_file=r"\\workdir\file.rst",
        material_file=r"\\workdir\engd.xml",
    )

    assert rd.name == "my first result definition"

    for k, v in defaults.items():
        assert getattr(rd, k) == v

    for v in _SUPPORTED_EXPRESSIONS:
        rd.expression = v
        assert rd.expression == v

    rd.combined_failure_criterion = cfc
    assert rd.combined_failure_criterion.name == "max strain & max stress"

    for v in _SUPPORTED_MEASURES:
        rd.measure = v
        assert rd.measure == v

    assert len(rd.scopes) == 1
    rd.scopes[0].mapping_file = r"\\workdir\solid_model.mapping"
    assert rd.scopes[0].composite_definition == r"\\workdir\ACPCompositeDefinitions.h5"
    assert rd.scopes[0].mapping_file == r"\\workdir\solid_model.mapping"
    assert rd.rst_file == r"\\workdir\file.rst"
    assert rd.material_file == r"\\workdir\engd.xml"

    rd.scopes[0].write_data_for_full_element_scope = False
    assert rd.scopes[0].write_data_for_full_element_scope == False

    rd.scopes[0].element_scope = [1, 2, 5]
    assert rd.scopes[0].element_scope == [1, 2, 5]

    rd.scopes[0].ply_scope = ["ply 1", "ply carbon UD"]
    assert rd.scopes[0].ply_scope == ["ply 1", "ply carbon UD"]

    rd.time = 2.3
    assert rd.time == 2.3

    rd.max_chunk_size = 7
    assert rd.max_chunk_size == 7

    ref_dict = {
        "version": 1,
        "accumulator": "max",
        "expression": "composite_failure",
        "failure_criteria_definition": {
            "criteria": {
                "max_strain": {
                    "active": True,
                    "eSxy": 0.0,
                    "e12": True,
                    "eSxz": 0.0,
                    "e13": False,
                    "e1": True,
                    "eXc": 0.0,
                    "eXt": 0.0,
                    "eSyz": 0.0,
                    "e23": False,
                    "e2": True,
                    "eYc": 0.0,
                    "eYt": 0.0,
                    "e3": False,
                    "eZc": 0.0,
                    "eZt": 0.0,
                    "force_global_strain_limits": False,
                    "wf_e1": 1.0,
                    "wf_e12": 1.0,
                    "wf_e13": 1.0,
                    "wf_e2": 1.0,
                    "wf_e23": 1.0,
                    "wf_e3": 1.0,
                },
                "max_stress": {
                    "active": True,
                    "s12": True,
                    "s13": False,
                    "s1": True,
                    "s23": False,
                    "s2": True,
                    "s3": False,
                    "wf_s1": 1.0,
                    "wf_s12": 1.0,
                    "wf_s13": 1.0,
                    "wf_s2": 1.0,
                    "wf_s23": 1.0,
                    "wf_s3": 1.0,
                },
            }
        },
        "measures": ["safety_factor"],
        "stress_strain_eval_mode": "rst_file",
        "time": 2.3,
        "max_chunk_size": 7,
        "scopes": [
            {
                "datasources": {
                    "composite_definition": ["\\\\workdir\\ACPCompositeDefinitions.h5"],
                    "assembly_mapping_file": ["\\\\workdir\\solid_model.mapping"],
                    "rst_file": ["\\\\workdir\\file.rst"],
                    "material_file": ["\\\\workdir\\engd.xml"],
                },
                "write_data_for_full_element_scope": False,
                "elements": [1, 2, 5],
                "ply_ids": ["ply 1", "ply carbon UD"],
            }
        ],
    }

    assert rd.to_dict() == ref_dict

    # test reprs
    rd._short_descr()
    rd.__repr__()