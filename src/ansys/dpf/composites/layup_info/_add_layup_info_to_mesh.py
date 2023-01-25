"""Helper functions to add layup information to a dpf Meshed Region."""
from typing import Optional

from ansys.dpf.core import MeshedRegion, Operator

from ..data_sources import CompositeDataSources
from .material_operators import MaterialOperators


def add_layup_info_to_mesh(
    data_sources: CompositeDataSources,
    material_operators: MaterialOperators,
    mesh: MeshedRegion,
    composite_definition_label: Optional[str] = None,
) -> Operator:
    """Add layup information to the mesh.

    Creates a Layup Provider Operator which is run and returned.

    Parameters
    ----------
    data_sources:
        DPF DataSources object available from CompositeModel: :class:`~CompositeModel.data_sources`
    mesh:
        DPF MeshedRegion object available from CompositeModel: :class:`~CompositeModel.get_mesh`
    material_operators:
       MaterialOperators object available from
       CompositeModel: :class:`~CompositeModel.material_operators`
    composite_definition_label:
        Label of composite definition
        (dictionary key in :class:`ContinuousFiberCompositesFiles.composite`).
        Only required for assemblies. See "Note on assemblies" in :class:`~CompositeModel`.
    Returns
    -------
    Layup Provider Operator
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

    # Set up the layup provider.
    # Reads the composite definition file and enriches the mesh
    # with the composite layup information.
    layup_provider = Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh)
    layup_provider.inputs.data_sources(data_sources.composite[composite_definition_label])
    layup_provider.inputs.abstract_field_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(
        material_operators.result_info_provider.outputs.result_info
    )
    layup_provider.run()

    return layup_provider
