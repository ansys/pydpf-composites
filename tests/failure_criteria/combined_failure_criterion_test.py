from ansys.dpf.composites.failure_criteria.combined_failure_criterion import CombinedFailureCriterion
from ansys.dpf.composites.failure_criteria.max_stress import MaxStressCriterion
from ansys.dpf.composites.failure_criteria.max_strain import MaxStrainCriterion

def test_combined_failure_criterion():

    cfc = CombinedFailureCriterion("my name")
    assert cfc.name == "my name"

    cfc.failure_criteria
    assert len(cfc.failure_criteria) == 0

    strain = MaxStrainCriterion()
    stress = MaxStressCriterion()
    cfc.insert(strain)
    cfc.insert(stress)

    assert len(cfc.failure_criteria) == 2

    removed = cfc.remove(strain.name)
    assert removed.name == "Max Strain"
    assert len(cfc.failure_criteria) == 1
    cfc.insert(stress)
    #still 1 FC because max stress was already added. Old entry is replaced
    assert len(cfc.failure_criteria) == 1
    cfc.insert(strain)

    attrs_d = cfc.to_dict()
    assert "max_stress" in attrs_d.keys()
    assert "max_strain" in attrs_d.keys()

    ref_d = {'max_stress': {'active': True, 's12': True, 's13': False, 's1': True,
                            's23': False, 's2': True, 's3': False,
                             'wf_s1': 1.0, 'wf_s12': 1.0, 'wf_s13': 1.0, 'wf_s2': 1.0, 'wf_s23': 1.0, 'wf_s3': 1.0
                            },
             'max_strain': {'active': True, 'eSxy': 0.0, 'e12': True, 'eSxz': 0.0, 'e13': False,
                            'e1': True, 'eXc': 0.0, 'eXt': 0.0, 'eSyz': 0.0, 'e23': False,
                            'e2': True, 'eYc': 0.0, 'eYt': 0.0, 'e3': False, 'eZc': 0.0, 'eZt': 0.0,
                            'force_global_strain_limits': False, 'wf_e1': 1.0, 'wf_e12': 1.0, 'wf_e13': 1.0, 'wf_e2': 1.0,
                            'wf_e23': 1.0, 'wf_e3': 1.0
                            }
             }

    assert attrs_d == ref_d

    #test repr
    cfc



