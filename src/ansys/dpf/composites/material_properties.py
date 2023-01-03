"""Helpers to get material properties."""
from typing import Collection, Dict, Union, cast

from ansys.dpf.core import DataSources, MeshedRegion, Operator, types
import numpy as np

from ansys.dpf.composites.enums import MaterialProperty
from ansys.dpf.composites.layup_info import get_dpf_material_id_by_analyis_ply_map


def get_constant_property(
    material_property: MaterialProperty,
    dpf_material_id: np.int64,
    materials_provider: Operator,
    data_source_or_streams_provider: Union[DataSources, Operator],
) -> float:
    """Get a constant material property.

    Only constant properties
    are supported. Variable properties are evaluated at their
    default value.

    Parameters
    ----------
    material_property:
        material property
    dpf_material_id:
    materials_provider:
        Dpf Materials provider operator
    data_source_or_streams_provider:
        Data source or streams provider that contains a rst file
    """
    material_property_field = Operator("eng_data::ans_mat_property_field_provider")
    material_property_field.inputs.materials_container(materials_provider)
    material_property_field.inputs.dpf_mat_id(int(dpf_material_id))
    material_property_field.inputs.property_name(material_property.value)
    result_info_provider = Operator("ResultInfoProvider")
    if isinstance(data_source_or_streams_provider, DataSources):
        result_info_provider.inputs.data_sources(data_source_or_streams_provider)
    else:
        result_info_provider.inputs.streams_container(data_source_or_streams_provider)
    material_property_field.inputs.unit_system_or_result_info(result_info_provider)
    properties = material_property_field.get_output(output_type=types.fields_container)
    assert len(properties) == 1, "Properties Container has to have exactly one entry"
    assert len(properties[0].data) == 1, (
        "Properties Field as to have exactly one entry. "
        "Probably the property is not constant. "
        "Variable properties are currently not supported."
    )
    return cast(float, properties[0].data[0])


def get_all_dpf_material_ids(
    mesh: MeshedRegion, data_source_or_streams_provider: Union[DataSources, Operator]
) -> Collection[np.int64]:
    """Get all the dpf_material_ids.

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
    material_properties: Collection[MaterialProperty],
    materials_provider: Operator,
    data_source_or_streams_provider: Union[DataSources, Operator],
    mesh: MeshedRegion,
) -> Dict[np.int64, Dict[MaterialProperty, float]]:
    """Get a dictionary with constant properties.

    Returns a dictionary with the dpf_material_id as key and
    a dict with the requested properties as the value. Only constant properties
    are supported. Variable properties are evaluated at their
    default value.
    This function can be expensive to evaluate and should not
    be called in a loop.

    Parameters
    ----------
    material_properties:
        Requested material properties
    materials_provider:
    data_source_or_streams_provider:
        Dpf DataSource or StreamProvider that contains a rst file
    mesh:
        Dpf MeshedRegion enriched with layup information
    """
    properties: Dict[np.int64, Dict[MaterialProperty, float]] = {}
    for dpf_material_id in get_all_dpf_material_ids(
        mesh=mesh, data_source_or_streams_provider=data_source_or_streams_provider
    ):
        properties[dpf_material_id] = {}
        for material_property in material_properties:
            constant_property = get_constant_property(
                material_property=material_property,
                dpf_material_id=dpf_material_id,
                materials_provider=materials_provider,
                data_source_or_streams_provider=data_source_or_streams_provider,
            )
            properties[dpf_material_id][material_property] = constant_property
    return properties
