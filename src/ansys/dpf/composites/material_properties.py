"""Helpers to get material properties."""
from typing import Collection, Dict, Union, cast

from ansys.dpf.core import DataSources, MeshedRegion, Operator, types

from ansys.dpf.composites.layup_info import get_dpf_material_id_by_analyis_ply_map


def get_constant_property(
    property_name: str,
    dpf_material_id: int,
    materials_provider: Operator,
    rst_data_source: DataSources,
) -> float:
    """Get a constant material property.

    Parameters
    ----------
    property_name:
        material property name (todo: document)
    dpf_material_id:
        dpf material id
    materials_provider:
        Dpf Materials provider operator
    rst_data_source:
        Dpf Data source that contains a rst file
    """
    material_property_field = Operator("eng_data::ans_mat_property_field_provider")
    material_property_field.inputs.materials_container(materials_provider)
    material_property_field.inputs.dpf_mat_id(dpf_material_id)
    material_property_field.inputs.property_name(property_name)
    result_info_provider = Operator("ResultInfoProvider")
    result_info_provider.inputs.data_sources(rst_data_source)
    material_property_field.inputs.unit_system_or_result_info(result_info_provider)
    return cast(
        float, material_property_field.get_output(output_type=types.fields_container)[0].data[0]
    )


def get_all_material_ids(
    mesh: MeshedRegion, data_source_or_streams_provider: Union[DataSources, Operator]
) -> Collection[int]:
    """Get all the dpf material ids.

    Parameters
    ----------
    mesh:
        Dpf MeshedRegion enriched with layup information
    data_source_or_streams_provider:
        Dpf DataSource or StreamProvider that contains a rst file
    """
    id_to_material_map = get_dpf_material_id_by_analyis_ply_map(
        mesh, data_source_or_streams_provider
    )
    return set(id_to_material_map.values())


def get_constant_property_dict(
    property_name: str,
    materials_provider: Operator,
    rst_data_source: DataSources,
    mesh: MeshedRegion,
) -> Dict[int, float]:
    """Get a dictionary with constant properties.

    Parameters
    ----------
    mesh:
        Dpf MeshedRegion enriched with layup information
    data_source_or_streams_provider:
        Dpf DataSource or StreamProvider that contains a rst file
    """
    properties = {}
    for id in get_all_material_ids(mesh, rst_data_source):
        property = get_constant_property(
            property_name=property_name,
            dpf_material_id=id,
            materials_provider=materials_provider,
            rst_data_source=rst_data_source,
        )
        properties[id] = property
    return properties
