"""Helper functions to add layup information to a dpf Meshed Region."""
from dataclasses import dataclass

from ansys.dpf.core import DataSources, MeshedRegion, Operator

from ansys.dpf.composites.example_helper.example_helper import ContinuousFiberCompositesFiles
from ansys.dpf.composites.material_setup import MaterialOperators, get_material_operators


@dataclass(frozen=True)
class LayupOperators:
    """Operators related to the composite Layup."""

    material_operators: MaterialOperators
    layup_provider: Operator


@dataclass(frozen=True)
class CompositeDataSources:
    """Data Sources related to the composite Layup."""

    rst: DataSources
    composites: DataSources


def get_composites_data_sources(
    composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create dpf data sources from a LongFibercompositeFiles object.

    Parameters
    ----------
    composite_files
    """
    rst_data_source = DataSources(composite_files.rst)
    composite_data_source = DataSources()
    composite_data_source.add_file_path(composite_files.engineering_data, "EngineeringData")
    composite_data_source.add_file_path(
        composite_files.composite_definitions, "CompositeDefinitions"
    )

    return CompositeDataSources(rst=rst_data_source, composites=composite_data_source)


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
        rst_data_source=data_sources.rst, engineering_data_source=data_sources.composites
    )

    # Set up the layup provider.
    # Reads the composite definition file and enriches the mesh
    # with the composite layup information.
    layup_provider = Operator("composite::layup_provider_operator")
    layup_provider.inputs.mesh(mesh)
    layup_provider.inputs.data_sources(data_sources.composites)
    layup_provider.inputs.abstract_field_support(
        material_operators.material_support_provider.outputs.abstract_field_support
    )
    layup_provider.inputs.unit_system_or_result_info(
        material_operators.result_info_provider.outputs.result_info
    )
    layup_provider.run()

    return LayupOperators(material_operators=material_operators, layup_provider=layup_provider)
