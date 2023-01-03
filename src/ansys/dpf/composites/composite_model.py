"""Composite Model."""
from dataclasses import dataclass
from typing import Collection, Dict, Optional, Sequence, cast

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .add_layup_info_to_mesh import LayupOperators, add_layup_info_to_mesh
from .composite_data_sources import (
    CompositeDataSources,
    ContinuousFiberCompositesFiles,
    get_composites_data_sources,
)
from .enums import FailureMeasure, LayerProperty, MaterialProperty
from .failure_criteria import CombinedFailureCriterion
from .layup_info import ElementInfo, LayupPropertiesProvider, get_element_info_provider
from .material_properties import get_constant_property_dict
from .result_definition import ResultDefinition
from .sampling_point import SamplingPoint


@dataclass(frozen=True)
class CompositeScope:
    """Composite scope.

    Defines which part of the model is selected.
    """

    elements: Optional[Sequence[int]] = None
    plies: Optional[Sequence[str]] = None
    time: Optional[float] = None


class CompositeModel:
    """Provides access to the basic composite post-processing functionality.

    On initialization, the CompositeModel automatically adds the composite layup information
    to the meshed region. It prepares the provider for different layup properties
    so they can be efficiently evaluated.

    Note: When creating a CompositeModel, several providers are created and
    the layup information is added the the dpf meshed region. Depending on the use
    case it can be more efficient to create the providers separately.

    Parameters
    ----------
    composite_files:

    """

    def __init__(self, composite_files: ContinuousFiberCompositesFiles, server: BaseServer):
        """Initialize data providers and add composite information to MeshedRegion."""
        self._core_model = dpf.Model(composite_files.rst, server=server)
        self._server = server

        self._composite_files = composite_files
        self._data_sources = get_composites_data_sources(composite_files)
        self._mesh: MeshedRegion = self._core_model.metadata.mesh_provider.outputs.mesh()
        self._layup_operators = add_layup_info_to_mesh(
            mesh=self.mesh, data_sources=self.data_sources
        )

        self._element_info_provider = get_element_info_provider(
            mesh=self.mesh,
            stream_provider_or_data_source=self._core_model.metadata.streams_provider,
        )
        self._layup_properties_provider = LayupPropertiesProvider(
            layup_provider=self._layup_operators.layup_provider, mesh=self.mesh
        )

    @property
    def mesh(self) -> MeshedRegion:
        """Get the underlying dpf meshed region.

        The meshed region also contains the layup information
        """
        return self._mesh

    @property
    def data_sources(self) -> CompositeDataSources:
        """Get the composite DataSources."""
        return self._data_sources

    @property
    def core_model(self) -> dpf.Model:
        """Get the underlying dpf core Model."""
        return self._core_model

    @property
    def layup_operators(self) -> LayupOperators:
        """Get the layup operators."""
        return self._layup_operators

    def evaluate_failure_criteria(
        self,
        combined_criteria: CombinedFailureCriterion,
        composite_scope: Optional[CompositeScope] = None,
        measure: FailureMeasure = FailureMeasure.inverse_reserve_factor,
        write_data_for_full_element_scope: bool = True,
    ) -> FieldsContainer:
        """Get a fields container with the evaluted failure criteria.

        The container contains the maximum per element if the measure
        is `FailureMeasure.inverse_reserve_factor` and the minimum per element
        if the measure is `FailureMeasure.margin_of_safety` or `FailureMeasure.reserve_factor`

        Parameters
        ----------
        combined_criteria:
            Combined failure criterion to evaluate
        composite_scope:
            Composite scope on which the failure criteria are evaluated. If
            empty, the criteria is evaluated on the full model.
        measure:
            Failure measure to evaluate
        write_data_for_full_element_scope:
            If True, each requested element in element scope gets a
            (potentially zero) failure value,
            even for elements which are not part of composite_scope.plies.
            If no element scope is specified (composite_scope.elements),
            a (potentially zero) failure value is written for all elements.
            Note: Due to a current limitation, it is sometimes needed to set
            write_data_for_full_element_scope to False, in particular if
            special element types such as beams are used in the model.
        """
        if composite_scope is None:
            composite_scope = CompositeScope()
        element_scope_in = [] if composite_scope.elements is None else composite_scope.elements
        ply_scope_in = [] if composite_scope.plies is None else composite_scope.plies
        if composite_scope.time is not None:
            time_in = composite_scope.time
        else:
            time_in = self.get_result_times_or_frequencies()[-1]

        if composite_scope.plies is None or len(composite_scope.plies):
            # This is a workaround, because setting the
            # write_data_for_full_element_scope flag to True can lead to
            # problems with 2023R1 if non-composite elements exists
            # in the solution such as beams. Since the flag
            # is irrelevant for cases without a ply scope we set it to False here
            write_data_for_full_element_scope = False

        rd = ResultDefinition(
            name="combined failure criteria",
            rst_files=[self._composite_files.rst],
            material_files=[self._composite_files.engineering_data],
            composite_definitions=[self._composite_files.composite_definitions],
            assembly_mapping_files=self._composite_files.mapping_files,
            combined_failure_criterion=combined_criteria,
            element_scope=element_scope_in,
            ply_scope=ply_scope_in,
            time=time_in,
            write_data_for_full_element_scope=write_data_for_full_element_scope,
            measures=[measure.value],
        )
        failure_operator = dpf.Operator("composite::composite_failure_operator")

        failure_operator.inputs.result_definition(rd.to_json())

        if measure == FailureMeasure.inverse_reserve_factor:
            return failure_operator.outputs.fields_containerMax()
        else:
            return failure_operator.outputs.fields_containerMin()

    def get_sampling_point(
        self,
        combined_criteria: CombinedFailureCriterion,
        element_id: int,
        time: Optional[float] = None,
    ) -> SamplingPoint:
        """Get a sampling point for a given element_id and failure criteria.

        Parameters
        ----------
        combined_criteria:
            Combined failiure critieron to evaluate
        element_id:
            Element Id/Label of the sampling point
        time:
            Time at which sampling point is evaluated
        """
        if time is None:
            time_in = self.get_result_times_or_frequencies()[-1]
        else:
            time_in = time

        rd = ResultDefinition(
            name="combined failure criteria",
            rst_files=[self._composite_files.rst],
            material_files=[self._composite_files.engineering_data],
            composite_definitions=[self._composite_files.composite_definitions],
            combined_failure_criterion=combined_criteria,
            element_scope=[element_id],
            time=time_in,
        )

        return SamplingPoint("Sampling Point", rd, server=self._server)

    def get_element_info(self, element_id: int) -> Optional[ElementInfo]:
        """Get element info for a given element id.

        Returns None if element type is not supported.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._element_info_provider.get_element_info(element_id)

    def get_property_for_all_layers(
        self, layup_property: LayerProperty, element_id: int
    ) -> Optional[NDArray[np.double]]:
        """Get a layer property for a given element_id.

        Returns a numpy array with the values of the property for all the layers.
        Values are ordered from bottom to top.
        Returns None if the element is not layered

        Parameters
        ----------
        layup_property:
            Selected layup property
        element_id:
            Selected element Id/Label
        """
        if layup_property == LayerProperty.angles:
            return self._layup_properties_provider.get_layer_angles(element_id)
        if layup_property == LayerProperty.thicknesses:
            return self._layup_properties_provider.get_layer_thicknesses(element_id)
        if layup_property == LayerProperty.shear_angles:
            return self._layup_properties_provider.get_layer_shear_angles(element_id)
        raise RuntimeError(f"Invalid property {layup_property}")

    def get_analysis_plies(self, element_id: int) -> Optional[Collection[str]]:
        """Get analysis ply names. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._layup_properties_provider.get_analysis_plies(element_id)

    def get_element_laminate_offset(self, element_id: int) -> Optional[np.double]:
        """Get laminate offset of element. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        """
        return self._layup_properties_provider.get_element_laminate_offset(element_id)

    def get_constant_property_dict(
        self, material_properties: Collection[MaterialProperty]
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
            A list of the requested material properties
        """
        return get_constant_property_dict(
            material_properties=material_properties,
            materials_provider=self.layup_operators.material_operators.material_provider,
            data_source_or_streams_provider=self.core_model.metadata.streams_provider,
            mesh=self.mesh,
        )

    def get_result_times_or_frequencies(self) -> NDArray[np.double]:
        """Return the last time value in the result file."""
        return cast(
            NDArray[np.double], self._core_model.metadata.time_freq_support.time_frequencies.data
        )

    def add_interlaminar_normal_stresses(
        self, stresses: FieldsContainer, strains: FieldsContainer
    ) -> None:
        """Add interlaminar_normal_stresses to the stresses FieldsContainer.

        Parameters
        ----------
        stresses:
            Stresses FieldsContainer
            (interlaminar normal stresses are added to this container)
        strains:
        """
        ins_operator = dpf.Operator("composite::interlaminar_normal_stress_operator")
        ins_operator.inputs.materials_container(
            self.layup_operators.material_operators.material_provider
        )
        ins_operator.inputs.mesh(self.mesh)
        ins_operator.inputs.mesh_properties_container(
            self.layup_operators.layup_provider.outputs.mesh_properties_container
        )
        # pass inputs by pin because the input name is not set yet.
        # Will be improved in sever version 2023 R2
        ins_operator.connect(24, self.layup_operators.layup_provider.outputs.fields_container)
        ins_operator.connect(0, strains)
        ins_operator.connect(1, stresses)

        # call run because ins operator has not output
        ins_operator.run()
