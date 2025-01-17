from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.failure_criteria import (
    CombinedFailureCriterion,
    CoreFailureCriterion,
    MaxStrainCriterion,
    MaxStressCriterion,
    VonMisesCriterion,
)
from ansys.dpf.composites.server_helpers import connect_to_or_start_server
from ansys.dpf.composites.data_sources import ContinuousFiberCompositesFiles, CompositeDefinitionFiles
from ansys.dpf.core import unit_systems
import os

server = connect_to_or_start_server()

solver_dir = r'D:\ANSYSDev\dpf_composites\test_data\lsdyna\shell_model'

composite_files = ContinuousFiberCompositesFiles(
    files_are_local=True,
    rst=[os.path.join(solver_dir, 'd3plot')],
    composite={"shell": CompositeDefinitionFiles(
        mapping=None,
        definition=os.path.join(solver_dir, 'ACPCompositeDefinitions.h5'),
    )
    },
    engineering_data=os.path.join(solver_dir, 'material.engd'),
    solver_input_file=os.path.join(solver_dir, 'input.k')
)

composite_model = CompositeModel(
    composite_files=composite_files,
    server=server,
    default_unit_system=unit_systems.solver_nmm
)

element_info_1 = composite_model.get_element_info(1)
element_info_2 = composite_model.get_element_info(2)
print(element_info_1)
print(element_info_2)

combined_fc = CombinedFailureCriterion(
    name="failure of all materials",
    failure_criteria=[
        MaxStrainCriterion(),
        MaxStressCriterion(),
        CoreFailureCriterion(),
        VonMisesCriterion(vme=True, vms=False),
    ],
)

composite_model