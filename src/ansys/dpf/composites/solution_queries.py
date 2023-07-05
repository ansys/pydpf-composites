import dataclasses
from functools import partial
from typing import Collection, Optional

import ansys.dpf.core as dpf
from ansys.dpf.core import MeshedRegion
import numpy as np

from ansys.dpf.composites._indexer import FieldIndexerWithDataPointer
from ansys.dpf.composites.composite_model import CompositeModel
from ansys.dpf.composites.constants import Spot
from ansys.dpf.composites.layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfoProvider,
    get_element_info_provider,
)
from ansys.dpf.composites.select_indices import (
    get_selected_indices,
    get_selected_indices_by_analysis_ply,
    get_selected_indices_by_dpf_material_ids,
)


@dataclasses.dataclass(frozen=True)
class SolutionFilter:
    layers: Optional[Collection[int]] = None
    nodes: Optional[Collection[int]] = None
    spots: Optional[Collection[Spot]] = None
    components: Optional[Collection[int]] = None


class LayeredDataProvider:
    def __init__(self, result_field, element_info_provider: ElementInfoProvider):
        self._result_field = result_field
        self._element_info_provider = element_info_provider

    def get_layered_data(self, element_id):
        element_info = self._element_info_provider.get_element_info(element_id)

        flat_indices = np.arange(
            0,
            (
                element_info.n_spots
                * element_info.number_of_nodes_per_spot_plane
                * element_info.n_layers
            ),
        )
        unraveled_indices = np.unravel_index(
            flat_indices,
            (
                element_info.n_layers,
                element_info.n_spots,
                element_info.number_of_nodes_per_spot_plane,
            ),
        )

        layer_indices = unraveled_indices[0]
        spot_indices = unraveled_indices[1]
        node_indices = unraveled_indices[2]
        data = self._result_field.get_entity_data_by_id(element_id)
        return LayeredData(
            data=data,
            layer_indices=layer_indices,
            spot_indices=spot_indices,
            node_indices=node_indices,
        )


class LayeredData:
    def __init__(self, data, layer_indices, spot_indices, node_indices):
        self.layer_indices = layer_indices
        self.spot_indices = spot_indices
        self.node_indices = node_indices
        # Todo return also material indices
        self.data = data

    def filter(self, layer_filter: SolutionFilter):
        filters = []
        if len(layer_filter.layers) > 0:
            filters.append(np.isin(self.layer_indices, layer_filter.layers))

        if len(layer_filter.nodes) > 0:
            filters.append(np.isin(self.node_indices, layer_filter.nodes))

        if len(layer_filter.spots) > 0:
            filters.append(np.isin(self.spot_indices, layer_filter.spots))

        filter = np.logical_and.reduce(filters)

        return LayeredData(
            data=self.data[filter],
            layer_indices=self.layer_indices[filter],
            node_indices=self.node_indices[filter],
            spot_indices=self.spot_indices[filter],
        )


def get_layered_data(data_provider: LayeredDataProvider, selector, accumlate_fun):
    result_field = dpf.field.Field(location=dpf.locations.elemental, nature=dpf.natures.scalar)
    indexer = FieldIndexerWithDataPointer(data_provider._result_field)
    element_ids = data_provider._result_field.scoping.ids
    with result_field.as_local_field() as local_result_field:
        for element_id in element_ids:
            # 0.2 s
            elementary_data = indexer.by_id(entity_id=element_id)
            # 0.8 s
            element_info = data_provider._element_info_provider.get_element_info(element_id)

            if not element_info.is_layered:
                continue
            selected_indices = selector(element_info=element_info)
            if len(selected_indices) > 0:
                elementary_data = elementary_data[selected_indices]
                # 1.1s

                if len(elementary_data) > 0:
                    if accumlate_fun is not None:
                        elementary_data = [accumlate_fun(elementary_data)]
                    # 1.4
                    local_result_field.append(elementary_data, scopingid=element_id)
                # 1.6s
    return result_field


def get_filter_selector(solution_filter: SolutionFilter):
    return partial(
        get_selected_indices,
        layers=solution_filter.layers,
        nodes=solution_filter.nodes,
        spots=solution_filter.spots,
    )


def get_analysis_ply_selector(analysis_ply_info_provider: AnalysisPlyInfoProvider):
    def inner(element_info):
        try:
            return get_selected_indices_by_analysis_ply(
                analysis_ply_info_provider=analysis_ply_info_provider, element_info=element_info
            )
        except Exception as e:
            return []

    return inner


def get_material_selector(dpf_material_ids: Collection[np.int64]):
    return partial(
        get_selected_indices_by_dpf_material_ids,
        dpf_material_ids=dpf_material_ids,
    )


class StressSolution:
    def __init__(self, composite_model: CompositeModel, time_id: int):
        self._time_id = time_id
        self._composite_model = composite_model
        self._mesh = composite_model.get_mesh()
        self._element_info_provider = get_element_info_provider(
            self._mesh,
            stream_provider_or_data_source=composite_model.core_model.metadata.streams_provider,
            no_bounds_checks=False,
        )

    def get_layered_data(self, element_id):
        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(dpf.Scoping(ids=[element_id]))

        stress_field = stress_op.outputs.fields_container()[0]
        layered_data_provider = LayeredDataProvider(stress_field, self._element_info_provider)
        return layered_data_provider.get_layered_data(element_id)

    def get_by_analysis_ply(self, analysis_ply_name: str, components=None, accumulate_fun=None):
        analysis_ply_provider = AnalysisPlyInfoProvider(self._mesh, analysis_ply_name)
        selector = get_analysis_ply_selector(analysis_ply_provider)
        element_ids = analysis_ply_provider.ply_element_ids()
        mesh_scoping = dpf.Scoping(ids=element_ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)

        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )

    def get_by_material(self, dpf_material_id: int, components=None, accumulate_fun=None):
        """
        Filter the element ids first. Could be worth the effort for materials
        that only exists in part of the the model
        Maybe we could also precompute all the element_infos
        element_ids = [element_id for element_id in self._mesh.elements.scoping.ids
        if self._element_info_provider.get_element_info(element_id)
        and dpf_material_id in self._element_info_provider.get_element_info(element_id).dpf_material_ids
        ]
        """

        selector = get_material_selector(dpf_material_ids=[dpf_material_id])
        mesh_scoping = dpf.Scoping(ids=self._mesh.elements.scoping.ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)
        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )


class FailureSolution:
    def __init__(self, composite_model: CompositeModel, time_id: int):
        self._time_id = time_id
        self._composite_model = composite_model
        self._mesh = composite_model.get_mesh()
        self._element_info_provider = get_element_info_provider(
            self._mesh,
            stream_provider_or_data_source=composite_model.core_model.metadata.streams_provider,
            no_bounds_checks=False,
        )

    def get_layered_data(self, element_id):
        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(dpf.Scoping(ids=[element_id]))

        stress_field = stress_op.outputs.fields_container()[0]
        layered_data_provider = LayeredDataProvider(stress_field, self._element_info_provider)
        return layered_data_provider.get_layered_data(element_id)

    def get_by_analysis_ply(self, analysis_ply_name: str, components=None, accumulate_fun=None):
        analysis_ply_provider = AnalysisPlyInfoProvider(self._mesh, analysis_ply_name)
        selector = get_analysis_ply_selector(analysis_ply_provider)
        element_ids = analysis_ply_provider.ply_element_ids()
        mesh_scoping = dpf.Scoping(ids=element_ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)

        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )

    def get_by_material(self, dpf_material_id: int, components=None, accumulate_fun=None):
        """
        Filter the element ids first. Could be worth the effort for materials
        that only exists in part of the the model
        Maybe we could also precompute all the element_infos
        element_ids = [element_id for element_id in self._mesh.elements.scoping.ids
        if self._element_info_provider.get_element_info(element_id)
        and dpf_material_id in self._element_info_provider.get_element_info(element_id).dpf_material_ids
        ]
        """

        selector = get_material_selector(dpf_material_ids=[dpf_material_id])
        mesh_scoping = dpf.Scoping(ids=self._mesh.elements.scoping.ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)
        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )


class FailureSolution:
    def __init__(self, composite_model: CompositeModel, time_id: int):
        self._time_id = time_id
        self._composite_model = composite_model
        self._mesh = composite_model.get_mesh()
        self._element_info_provider = get_element_info_provider(
            self._mesh,
            stream_provider_or_data_source=composite_model.core_model.metadata.streams_provider,
            no_bounds_checks=False,
        )

    def get_layered_data(self, element_id):
        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(dpf.Scoping(ids=[element_id]))

        stress_field = stress_op.outputs.fields_container()[0]
        layered_data_provider = LayeredDataProvider(stress_field, self._element_info_provider)
        return layered_data_provider.get_layered_data(element_id)

    def get_by_analysis_ply(self, analysis_ply_name: str, components=None, accumulate_fun=None):
        analysis_ply_provider = AnalysisPlyInfoProvider(self._mesh, analysis_ply_name)
        selector = get_analysis_ply_selector(analysis_ply_provider)
        element_ids = analysis_ply_provider.ply_element_ids()
        mesh_scoping = dpf.Scoping(ids=element_ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)

        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )

    def get_by_material(self, dpf_material_id: int, components=None, accumulate_fun=None):
        """
        Filter the element ids first. Could be worth the effort for materials
        that only exists in part of the the model
        Maybe we could also precompute all the element_infos
        element_ids = [element_id for element_id in self._mesh.elements.scoping.ids
        if self._element_info_provider.get_element_info(element_id)
        and dpf_material_id in self._element_info_provider.get_element_info(element_id).dpf_material_ids
        ]
        """

        selector = get_material_selector(dpf_material_ids=[dpf_material_id])
        mesh_scoping = dpf.Scoping(ids=self._mesh.elements.scoping.ids)

        stress_op = self._composite_model.core_model.results.stress.on_all_time_freqs()
        stress_op.inputs.bool_rotate_to_global(False)
        stress_op.inputs.time_scoping(self._time_id)
        stress_op.inputs.mesh_scoping(mesh_scoping)
        if components is None:
            components = [0, 1, 2, 3, 4, 5]

        component_selector = dpf.operators.logic.component_selector()
        component_selector.inputs.field.connect(stress_op)
        component_selector.inputs.component_number(components)
        stress_field = component_selector.outputs.field()

        return get_layered_data(
            LayeredDataProvider(stress_field, self._element_info_provider),
            selector,
            accumlate_fun=accumulate_fun,
        )
