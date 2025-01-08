# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Methods to get ply-wise data from a result field."""

from enum import Enum, IntEnum

from ansys.dpf.core import Field, MeshedRegion, Operator, operators
from ansys.dpf.gate.common import locations

__all__ = ("SpotReductionStrategy", "get_ply_wise_data")


class SpotReductionStrategy(Enum):
    """Provides the strategy for getting from spot values (BOT, MID, TOP) to a single value."""

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
    spot_reduction_strategy: SpotReductionStrategy = SpotReductionStrategy.AVG,
    requested_location: str = locations.elemental_nodal,
    component: IntEnum | int = 0,
) -> Field:
    """Get ply-wise data from a field.

    Parameters
    ----------
    field:
        Field to extract data from.
    ply_name:
        Name of the ply to extract data from.
    mesh :
        Meshed region that needs to be enriched with composite information.
        Use the ``CompositeModel.get_mesh()`` method to get the meshed region.
    spot_reduction_strategy :
        Reduction strategy for getting from spot values (BOT, MID, TOP) to a single value
        per corner node and layer. The default is ``AVG``.
    requested_location :
        Location of the output field. Important: The function always averages nodal values
        for ``"elemental"`` or ``"nodal"`` locations,
        irrespective of ``"spot_reduction_strategy"``.
        Options are ``"elemental"``, ``"elemental_nodal"``, and ``"nodal"``.
        The default is ``"elemental_nodal"``.
    component :
        Component to extract data from. The default is ``0``.
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
    filter_ply_data_op.inputs.reduction_strategy(spot_reduction_strategy.value)
    elemental_nodal_data = filter_ply_data_op.outputs.field()

    if requested_location == locations.elemental_nodal:
        return elemental_nodal_data

    if requested_location == locations.elemental:
        # Note Jan 2024 we currently always average over the nodes in an element. It would also be
        # useful to be able to get the max or min value over the nodes in an element.
        # This could be done with the max_by_entity_operator but this workflow is currently
        # broken due to BUG 964544
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
