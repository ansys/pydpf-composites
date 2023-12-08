"""Methods to get ply wise data from a result field."""

from enum import Enum, IntEnum
from typing import Union

from ansys.dpf.core import Field, MeshedRegion, Operator, operators
from ansys.dpf.gate.common import locations

__all__ = ("ReductionStrategy", "get_ply_wise_data")


class ReductionStrategy(Enum):
    """The reduction strategy to get from spot values (BOT, MID, TOP) to a single value."""

    MIN = "MIN"
    MAX = "MAX"
    AVG = "AVG"
    BOT = "BOT"
    MID = "MID"
    TOP = "TOP"


def get_ply_wise_data(
    field: Field,
    ply_name: str,
    mesh: MeshedRegion,
    reduction_strategy: ReductionStrategy = ReductionStrategy.AVG,
    requested_location: str = locations.elemental_nodal,
    component: Union[IntEnum, int] = 0,
) -> Field:
    """Get ply-wise data from a field.

    Parameters
    ----------
    field:
        The field to extract data from.
    ply_name:
        The name of the ply to extract data from.
    mesh:
        The meshed region. Needs to be enriched with composite information.
        Use CompositeModel.get_mesh() to get the meshed region.
    reduction_strategy:
        The reduction strategy to get from spot values (BOT, MID, TOP) to a single value
        per corner node and layer. The default is AVG.
    requested_location:
        The location of the output field. The default is elemental_nodal. Supported are
        elemental_nodal, elemental, and nodal.
    component:
        The component to extract data from. Can be an int or an IntEnum. The default is 0.
    """
    component_int = component.value if isinstance(component, IntEnum) else component
    component_selector = operators.logic.component_selector()

    component_selector.inputs.field.connect(field)
    component_selector.inputs.component_number.connect(component_int)
    single_component_field = component_selector.outputs.field()

    filter_ply_data_op = Operator("composite::filter_ply_data_operator")
    filter_ply_data_op.inputs.field(single_component_field)
    filter_ply_data_op.inputs.mesh(mesh)
    filter_ply_data_op.inputs.ply_id(ply_name)
    filter_ply_data_op.inputs.reduction_strategy(reduction_strategy.value)
    elemental_nodal_data = filter_ply_data_op.outputs.field()

    if requested_location == locations.elemental_nodal:
        return elemental_nodal_data

    if requested_location == locations.elemental:
        elemental_nodal_to_elemental = operators.averaging.elemental_mean()
        elemental_nodal_to_elemental.inputs.field.connect(elemental_nodal_data)
        out_field = elemental_nodal_to_elemental.outputs.field()
        out_field.location = locations.elemental
        return out_field

    if requested_location == locations.nodal:
        elemental_nodal_to_nodal = operators.averaging.elemental_nodal_to_nodal()
        elemental_nodal_to_nodal.inputs.mesh.connect(mesh)
        elemental_nodal_to_nodal.inputs.field.connect(elemental_nodal_data)
        out_field = elemental_nodal_to_nodal.outputs.field()
        out_field.location = locations.nodal
        return out_field

    raise RuntimeError(
        f"Invalid requested location {requested_location}. "
        f"Valid locations are {locations.elemental_nodal}, "
        f"{locations.elemental}, and {locations.nodal}."
    )
