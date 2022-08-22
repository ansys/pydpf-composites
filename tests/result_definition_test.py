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
        assert rd.measures == [v]

    rd.composite_definitions = [r"\\workdir\ACPCompositeDefinitions.h5"]
    assert rd.composite_definitions == [r"\\workdir\ACPCompositeDefinitions.h5"]

    rd.assembly_mapping_files = [r"\\workdir\solid_model.mapping"]
    assert rd.assembly_mapping_files == [r"\\workdir\solid_model.mapping"]

    rd.rst_files = [r"\\workdir\file.rst"]
    assert rd.rst_files == [r"\\workdir\file.rst"]

    rd.material_files = [r"\\workdir\engd.xml"]
    assert rd.material_files == [r"\\workdir\engd.xml"]

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

    ref_dict = {'version': 1,
                'accumulator': 'max',
                'expression': 'sampling_point',
                'failure_criteria_definition':
                    {'criteria':
                         {'max_strain':
                              {'active': True, 'e12': 0.0, 'e12': True,
                               'e13': 0.0, 'e13': False, 'e1': True,
                               'e1c': 0.0, 'e1t': 0.0, 'e23': 0.0,
                               'e23': False, 'e2': True, 'e2c': 0.0,
                               'e2t': 0.0, 'e3': False, 'e3c': 0.0,
                               'e3t': 0.0, 'force_global_limits': False,
                               'wf_e1': 1.0, 'wf_e12': 1.0, 'wf_e13': 1.0,
                               'wf_e2': 1.0, 'wf_e23': 1.0, 'wf_e3': 1.0},
                          'max_stress': {'active': True, 's12': True,
                                         's13': False, 's1': True, 's23': False,
                                         's2': True, 's3': False, 'wf_s1': 1.0, 'wf_s12': 1.0,
                                         'wf_s13': 1.0, 'wf_s2': 1.0, 'wf_s23': 1.0, 'wf_s3': 1.0}
                          }
                     },
                'measures': ['safety_margin'],
                'stress_strain_eval_mode': 'rst_file',
                'time': 2.3,
                'max_chunk_size': 7,
                'scopes': [{'datasources':
                                {'composite_definition': ['\\\\workdir\\ACPCompositeDefinitions.h5'],
                                 'assembly_mapping_files': ['\\\\workdir\\solid_model.mapping'],
                                 'rst_file': ['\\\\workdir\\file.rst'],
                                 'material_file': ["\\\\workdir\\engd.xml"]
                                 },
                            'write_data_for_full_element_scope': False,
                            'elements': [1, 2, 5],
                            'ply_ids': ['ply 1', 'ply carbon UD']
                            }
                           ]
                }

    ref_json = '{"version": 1, "accumulator": "max", "expression": "sampling_point", "failure_criteria_definition": ' \
               '{"criteria": {"max_strain": {"active": true, "e12": 0.0, "e12": true, "e13": 0.0, ' \
               '"e13": false, "e1": true, "e1c": 0.0, "e1t": 0.0, "e23": 0.0, "e23": false, ' \
               '"e2": true, "e2c": 0.0, "e2t": 0.0, "e3": false, "e3c": 0.0, "e3t": 0.0, ' \
               '"force_global_limits": false, "wf_e1": 1.0, "wf_e12": 1.0, "wf_e13": 1.0, "wf_e2": 1.0, "wf_e23": 1.0,' \
               ' "wf_e3": 1.0}, "max_stress": {"active": true, "s12": true, "s13": false, ' \
               '"s1": true, "s23": false, "s2": true, "s3": false, "wf_s1": 1.0, ' \
               '"wf_s12": 1.0, "wf_s13": 1.0, "wf_s2": 1.0, "wf_s23": 1.0, "wf_s3": 1.0}}}, ' \
               '"measures": ["safety_margin"], "stress_strain_eval_mode": "rst_file", "time": 2.3, ' \
               '"max_chunk_size": 7, ' \
               '"scopes": [{"datasources": {"composite_definition": ["\\\\\\\\workdir\\\\ACPCompositeDefinitions.h5"], ' \
               '"assembly_mapping_files": ["\\\\\\\\workdir\\\\solid_model.mapping"], ' \
               '"rst_file": ["\\\\\\\\workdir\\\\file.rst"], "material_file": ["\\\\\\\\workdir\\\\engd.xml"]}, ' \
               '"write_data_for_full_element_scope": false, "elements": [1, 2, 5], ' \
               '"ply_ids": ["ply 1", "ply carbon UD"]}]}'

    assert rd.to_dict() == ref_dict
    assert rd.to_json_dict() == ref_json

    # test reprs
    rd._short_descr()

