from ansys.dpf.composites.result_definition import (ResultDefinition,
                                                    _SUPPORTED_EXPRESSIONS,
                                                    _SUPPORTED_MEASURES,
                                                    _SUPPORTED_STRESS_STRAIN_EVAL_MODES
                                                    )
from ansys.dpf.composites.failure_criteria.combined_failure_criterion import CombinedFailureCriterion
from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion
from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion

defaults = {"expression": "composite_failure",
            "combined_failure_criterion": None,
            "measures": ["inverse_reserve_factor"],
            "composite_definitions": [],
            "assembly_mapping_files": [],
            "rst_files": [],
            "material_files": [],
            "write_data_for_full_element_scope": True,
            "element_scope":[],
            "ply_scope": [],
            "stress_strain_eval_mode": "rst_file",
            "time": 1.,
            "max_chunk_size":50000
            }

def test_result_definition():
    cfc = CombinedFailureCriterion("max strain & max stress")
    cfc.insert(MaxStrainCriterion())
    cfc.insert(MaxStressCriterion())

    rd = ResultDefinition("my first result definition")
    assert rd.name == "my first result definition"

    for k, v in defaults.items():
        assert getattr(rd, k) == v

    for v in _SUPPORTED_EXPRESSIONS:
        rd.expression = v
        assert rd.expression == v

    rd.combined_failure_criterion = cfc
    assert rd.combined_failure_criterion.name == "max strain & max stress"

    for v in _SUPPORTED_MEASURES:
        rd.measures = [v]
        assert rd.expression == [v]

    rd.composite_definitions = [r"\\workdir\ACPCompositeDefinitions.h5"]
    assert rd.composite_definitions == [r"\\workdir\ACPCompositeDefinitions.h5"]

    rd.assembly_mapping_files = [r"\\workdir\solid_model.mapping"]
    assert rd.assembly_mapping_files == [r"\\workdir\solid_model.mapping"]

    rd.rst_files = [r"\\workdir\file.rst"]
    assert rd.rst_files == [r"\\workdir\file.rst"]

    rd.material_files = ["'\\workdir\engd.xml"]
    assert rd.material_files == ["'\\workdir\engd.xml"]

    rd.write_data_for_full_element_scope = False
    assert rd.write_data_for_full_element_scope == False

    rd.element_scope = [1,2, 5]
    assert rd.element_scope == [1, 2, 5]

    rd.ply_scope = ["ply 1", "ply carbon UD"]
    assert rd.ply_scope == ["ply 1", "ply carbon UD"]

    rd.time = 2.3
    assert rd.time == 2.3

    rd.max_chunk_size = 7
    assert rd.max_chunk_size == 7

    rd.to_dict()
    rd.to_json_dict()

    # test reprs
    rd._short_descr()

