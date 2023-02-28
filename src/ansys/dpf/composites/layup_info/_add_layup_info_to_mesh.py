"""Helper functions to add lay-up information to a DPF meshed region."""
from typing import Optional
from warnings import warn

from ansys.dpf.core import MeshedRegion, Operator

from ..data_sources import CompositeDataSources
from ..unit_system import UnitSystemProvider
from .material_operators import MaterialOperators


def add_layup_info_to_mesh(
    data_sources: CompositeDataSources,
    material_operators: MaterialOperators,
    mesh: MeshedRegion,
    unit_system: Optional[UnitSystemProvider] = None,
    composite_definition_label: Optional[str] = None,
) -> Operator:
    """Add lay-up information to the mesh.

    Creates a lay-up provider operator that is run and returned.

    Parameters
    ----------
    data_sources:
        DPF data sources available from the :attr:`.CompositeModel.data_sources` attribute.
    mesh:
        DPF meshed region available from the :meth:`.CompositeModel.get_mesh` method.
    material_operators:
       MaterialOperators object available from the :attr:`.CompositeModel.material_operators`
       attribute.
    unit_system:
        Unit system specification
    composite_definition_label:
        Label of the composite definition, which is the
        dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
        attribute. This parameter is only required for assemblies.
        See the note about assemblies in the description for the :class:`.CompositeModel` class.
    Returns
    -------
    :
        Lay-up provider operator.
    """
    if composite_definition_label is None:
        composite_definition_labels = list(data_sources.composite.keys())
        if len(composite_definition_labels) == 1:
            composite_definition_label = composite_definition_labels[0]
        else:
            raise RuntimeError(
                f"Multiple composite definition keys exists: {composite_definition_labels}. "
                f"Please specify a key explicitly."
            )

    # Set up the lay-up provider.
    # Reads the composite definition file and enriches the mesh
    # with the composite lay-up information.
    layup_provider = Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh)
    layup_provider.inputs.data_sources(data_sources.composite[composite_definition_label])
    layup_provider.inputs.abstract_field_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )

    if unit_system is None:
        warn(
            "Calling add_layup_info_to_mesh"
            "without a unit system is deprecated. Use get_unit_system"
            "to obtain the unit system.",
            DeprecationWarning,
            stacklevel=2,
        )
        unit_system = material_operators.result_info_provider

    layup_provider.inputs.unit_system(unit_system)
    layup_provider.run()

    return layup_provider
