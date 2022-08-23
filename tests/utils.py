from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion
from ansys.dpf.composites.failure_criteria import MaxStressCriterion
from ansys.dpf.composites.failure_criteria import MaxStrainCriterion
from ansys.dpf.composites.failure_criteria import TsaiHillCriterion
from ansys.dpf.composites.failure_criteria import TsaiWuCriterion
from ansys.dpf.composites.failure_criteria import HoffmanCriterion
from ansys.dpf.composites.failure_criteria import HashinCriterion
from ansys.dpf.composites.failure_criteria import CuntzeCriterion
from ansys.dpf.composites.failure_criteria import CoreFailureCriterion
from ansys.dpf.composites.failure_criteria import VonMisesCriterion

def get_basic_combined_failure_criterion():
    max_strain = MaxStrainCriterion()
    max_stress = MaxStressCriterion()
    tsai_hill = TsaiHillCriterion()
    tsai_wu = TsaiWuCriterion()
    hoffman = HoffmanCriterion()
    hashin = HashinCriterion()
    cuntze = CuntzeCriterion()
    core_failure = CoreFailureCriterion()
    von_mises_strain_only = VonMisesCriterion(vme=True, vms=False)
    
    cfc = CombinedFailureCriterion()
    cfc.insert(max_strain)
    cfc.insert(max_stress)
    cfc.insert(tsai_hill)
    cfc.insert(tsai_wu)
    cfc.insert(hoffman)
    cfc.insert(hashin)
    cfc.insert(cuntze)
    cfc.insert(core_failure)
    cfc.insert(von_mises_strain_only)
    return cfc
