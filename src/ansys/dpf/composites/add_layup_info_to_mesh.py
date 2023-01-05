"""Helper functions to add layup information to a dpf Meshed Region."""
from dataclasses import dataclass
from typing import Optional

from ansys.dpf.core import MeshedRegion, Operator

from .composite_data_sources import CompositeDataSources
from .material_setup import MaterialOperators, get_material_operators


@dataclass(frozen=True)
class LayupOperators:
    """Operators related to the composite Layup.

    Parameters
    ----------
    material_operators:
    layup_provider:
        Layup provider operator. When run, adds composite information to
        the dpf MeshedRegion.
    """

    material_operators: MaterialOperators
    layup_provider: Operator


def add_layup_info_to_mesh(
    data_sources: CompositeDataSources,
    mesh: MeshedRegion,
    composite_definition_label: Optional[str] = None,
) -> LayupOperators:
    """Add layup information to the mesh.

    Parameters
    ----------
    data_sources
    mesh
    composite_definition_label:
        Label of composite definition (dictionary key in CompositeDataSources.composites_files)
    """
    if composite_definition_label is None:
        composite_definition_labels = list(data_sources.composites_files.keys())
        if len(composite_definition_labels) == 1:
            composite_definition_label = composite_definition_labels[0]
        else:
            raise RuntimeError(
                f"Multiple composite definition keys exists: {composite_definition_labels}. "
                f"Please specify a key explicitly."
            )

    material_operators = get_material_operators(
        rst_data_source=data_sources.rst, engineering_data_source=data_sources.engineering_data
    )

    # Set up the layup provider.
    # Reads the composite definition file and enriches the mesh
    # with the composite layup information.
    layup_provider = Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh)
    # todo: Handle multiple scopes
    layup_provider.inputs.data_sources(data_sources.composites_files[composite_definition_label])
    layup_provider.inputs.abstract_field_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(
        material_operators.result_info_provider.outputs.result_info
    )
    layup_provider.run()

    return LayupOperators(material_operators=material_operators, layup_provider=layup_provider)
