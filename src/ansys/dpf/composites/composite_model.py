"""Composite Model."""
from dataclasses import dataclass
from typing import Collection, Dict, List, Optional, Sequence, cast

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
from .result_definition import ResultDefinition, ResultDefinitionScope
from .sampling_point import SamplingPoint


@dataclass(frozen=True)
class CompositeScope:
    """Composite scope.

    Defines which part of the model is selected.
    """

    elements: Optional[Sequence[int]] = None
    plies: Optional[Sequence[str]] = None
    time: Optional[float] = None


class CompositeInfo:
    """Contains composite data providers for a given composite definition."""

    def __init__(
        self,
        data_sources: CompositeDataSources,
        composite_definition_label: str,
        streams_provider: dpf.Operator,
    ):
        """Initialize CompositeInfo and add enrich mesh with composite information."""
        mesh_provider = dpf.Operator("MeshProvider")
        mesh_provider.inputs.data_sources(data_sources.rst)
        self.mesh = mesh_provider.outputs.mesh()

        self.layup_operators = add_layup_info_to_mesh(
            mesh=self.mesh,
            data_sources=data_sources,
            composite_definition_label=composite_definition_label,
        )

        self.element_info_provider = get_element_info_provider(
            mesh=self.mesh,
            stream_provider_or_data_source=streams_provider,
        )
        self.layup_properties_provider = LayupPropertiesProvider(
            layup_provider=self.layup_operators.layup_provider, mesh=self.mesh
        )


class CompositeModel:
    """Provides access to the basic composite post-processing functionality.

    On initialization, the CompositeModel automatically adds the composite layup information
    to the meshed region(s). It prepares the providers for different layup properties
    so they can be efficiently evaluated.

    Note on performance: When creating a CompositeModel, several providers are created and
    the layup information is added the dpf meshed regions. Depending on the use
    case it can be more efficient to create the providers separately.

    Note on assemblies: For assemblies with multiple composite definition files, separate meshes and
    layup operators are generated (wrapped by CompositeInfo). This is needed because the
    layup provider can currently only add the data of a single composite definitions file
    to a mesh. All functions which depend on composite definitions have to be called with the
    correct composite_definition_label. The layered elements that got information from a given
    composite_definition_label can be determined by calling
    self.get_all_layered_element_ids_for_composite_definition_label.
     All the elements which are not part of a composite definition are either homogeneous
    solids or layered models defined outside of an ACP model.
    self.composite_definition_labels returns
    All the available composite_definition_labels.

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

        # todo: extract material operators only once
        self._composite_infos: Dict[str, CompositeInfo] = {}
        for composite_definition_label in self._data_sources.composite:
            self._composite_infos[composite_definition_label] = CompositeInfo(
                self._data_sources,
                composite_definition_label,
                self._core_model.metadata.streams_provider,
            )

    @property
    def composite_definition_labels(self) -> Sequence[str]:
        """Get all the composite_definition_labels in this model.

        Only relevant for assemblies.
        """
        return list(self._composite_infos.keys())

    def get_mesh(self, composite_definition_label: Optional[str] = None) -> MeshedRegion:
        """Get the underlying dpf meshed region.

        The meshed region also contains the layup information
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return self._composite_infos[composite_definition_label].mesh

    @property
    def data_sources(self) -> CompositeDataSources:
        """Get the composite DataSources."""
        return self._data_sources

    @property
    def core_model(self) -> dpf.Model:
        """Get the underlying dpf core Model."""
        return self._core_model

    def get_layup_operators(
        self, composite_definition_label: Optional[str] = None
    ) -> LayupOperators:
        """Get the layup operators."""
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return self._composite_infos[composite_definition_label].layup_operators

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

        scopes = []
        for composite_definition_label in self.composite_definition_labels:
            composite_files = self._composite_files.composite[composite_definition_label]
            scopes.append(
                ResultDefinitionScope(
                    composite_definition=composite_files.definition,
                    mapping_file=composite_files.mapping,
                    element_scope=element_scope_in,
                    ply_scope=ply_scope_in,
                    write_data_for_full_element_scope=write_data_for_full_element_scope,
                )
            )

        rd = ResultDefinition(
            name="combined failure criteria",
            rst_file=self._composite_files.rst,
            material_file=self._composite_files.engineering_data,
            combined_failure_criterion=combined_criteria,
            composite_scopes=scopes,
            time=time_in,
            measure=measure.value,
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
        composite_definition_label: Optional[str] = None,
    ) -> SamplingPoint:
        """Get a sampling point for a given element_id and failure criteria.

        Parameters
        ----------
        combined_criteria:
            Combined failure criterion to evaluate
        element_id:
            Element Id/Label of the sampling point
        time:
            Time at which sampling point is evaluated
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite).
            Only required for assemblies
        """
        if time is None:
            time_in = self.get_result_times_or_frequencies()[-1]
        else:
            time_in = time

        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()

        scope = ResultDefinitionScope(
            composite_definition=self._composite_files.composite[
                composite_definition_label
            ].definition,
            element_scope=[element_id],
            ply_scope=[],
        )
        rd = ResultDefinition(
            name="combined failure criteria",
            rst_file=self._composite_files.rst,
            material_file=self._composite_files.engineering_data,
            combined_failure_criterion=combined_criteria,
            time=time_in,
            composite_scopes=[scope],
        )

        return SamplingPoint("Sampling Point", rd, server=self._server)

    def get_element_info(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[ElementInfo]:
        """Get element info for a given element id.

        Returns None if element type is not supported.

        Parameters
        ----------
        element_id:
            Element Id/Label
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite_files).
            Only required for assemblies. See "Note on assemblies" in class docstring.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return self._composite_infos[
            composite_definition_label
        ].element_info_provider.get_element_info(element_id)

    def get_property_for_all_layers(
        self,
        layup_property: LayerProperty,
        element_id: int,
        composite_definition_label: Optional[str] = None,
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
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite).
            Only required for assemblies. See "Note on assemblies" in class docstring.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        layup_properties_provider = self._composite_infos[
            composite_definition_label
        ].layup_properties_provider
        if layup_property == LayerProperty.angles:
            return layup_properties_provider.get_layer_angles(element_id)
        if layup_property == LayerProperty.thicknesses:
            return layup_properties_provider.get_layer_thicknesses(element_id)
        if layup_property == LayerProperty.shear_angles:
            return layup_properties_provider.get_layer_shear_angles(element_id)
        raise RuntimeError(f"Invalid property {layup_property}")

    def get_analysis_plies(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[Collection[str]]:
        """Get analysis ply names. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite).
            Only required for assemblies. See "Note on assemblies" in class docstring.
            The dict will only contain the analysis plies in the specified composite definition.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        layup_properties_provider = self._composite_infos[
            composite_definition_label
        ].layup_properties_provider
        return layup_properties_provider.get_analysis_plies(element_id)

    def get_element_laminate_offset(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[np.double]:
        """Get laminate offset of element. Returns None if element is not layered.

        Parameters
        ----------
        element_id:
            Element Id/Label
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite).
            Only required for assemblies. See "Note on assemblies" in class docstring.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        layup_properties_provider = self._composite_infos[
            composite_definition_label
        ].layup_properties_provider
        return layup_properties_provider.get_element_laminate_offset(element_id)

    def get_constant_property_dict(
        self,
        material_properties: Collection[MaterialProperty],
        composite_definition_label: Optional[str] = None,
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
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite_files).
            Only required for assemblies. See "Note on assemblies" in class docstring.
            The dict will only contain the materials of the analysis plies defined
            in the specified composite definition.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return get_constant_property_dict(
            material_properties=material_properties,
            materials_provider=self.get_layup_operators(
                composite_definition_label
            ).material_operators.material_provider,
            data_source_or_streams_provider=self.core_model.metadata.streams_provider,
            mesh=self.get_mesh(composite_definition_label),
        )

    def get_result_times_or_frequencies(self) -> NDArray[np.double]:
        """Return the available times/frequencies in the result file."""
        return cast(
            NDArray[np.double], self._core_model.metadata.time_freq_support.time_frequencies.data
        )

    def add_interlaminar_normal_stresses(
        self,
        stresses: FieldsContainer,
        strains: FieldsContainer,
        composite_definition_label: Optional[str] = None,
    ) -> None:
        """Add interlaminar_normal_stresses to the stresses FieldsContainer.

        Parameters
        ----------
        stresses:
            Stresses FieldsContainer
            (interlaminar normal stresses are added to this container)
        strains:
        composite_definition_label:
            Label of composite definition
            (dictionary key in ContinuousFiberCompositesFiles.composite).
            Only required for assemblies. See "Note on assemblies" in class docstring.
            Interlaminar normal stresses are only added to the layered elements defined
            in the specified composite definition.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        layup_operators = self._composite_infos[composite_definition_label].layup_operators
        ins_operator = dpf.Operator("composite::interlaminar_normal_stress_operator")
        ins_operator.inputs.materials_container(
            layup_operators.material_operators.material_provider
        )
        ins_operator.inputs.mesh(self.get_mesh(composite_definition_label))
        ins_operator.inputs.mesh_properties_container(
            layup_operators.layup_provider.outputs.mesh_properties_container
        )
        # pass inputs by pin because the input name is not set yet.
        # Will be improved in sever version 2023 R2
        ins_operator.connect(24, layup_operators.layup_provider.outputs.fields_container)
        ins_operator.connect(0, strains)
        ins_operator.connect(1, stresses)

        # call run because ins operator has not output
        ins_operator.run()

    def get_all_layered_element_ids_for_composite_definition_label(
        self, composite_definition_label: str
    ) -> Sequence[int]:
        """Get all the layered element ids that belong to a given composite_definition_label."""
        return cast(
            List[int],
            self.get_mesh(composite_definition_label)
            .property_field("element_layer_indices")
            .scoping.ids,
        )

    def _first_composite_definition_label_if_only_one(self) -> str:
        if len(self.composite_definition_labels) == 1:
            return self.composite_definition_labels[0]
        else:
            raise RuntimeError(
                f"Multiple composite definition keys exists: {self.composite_definition_labels}. "
                f"Please specify a key explicitly."
            )
