"""Helper functions to add layup information to a dpf Meshed Region."""
from dataclasses import dataclass

from ansys.dpf.core import MeshedRegion, Operator

from ansys.dpf.composites.composite_data_sources import CompositeDataSources
from ansys.dpf.composites.material_setup import MaterialOperators, get_material_operators


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
    data_sources: CompositeDataSources, mesh: MeshedRegion
) -> LayupOperators:
    """Add layup information to the mesh.

    Parameters
    ----------
    data_sources
    mesh
    """
    material_operators = get_material_operators(
        rst_data_source=data_sources.rst, engineering_data_source=data_sources.composites_files
    )

    # Set up the layup provider.
    # Reads the composite definition file and enriches the mesh
    # with the composite layup information.
    layup_provider = Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh)
    layup_provider.inputs.data_sources(data_sources.composites_files)
    layup_provider.inputs.abstract_field_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(
        material_operators.result_info_provider.outputs.result_info
    )
    layup_provider.run()

    return LayupOperators(material_operators=material_operators, layup_provider=layup_provider)
