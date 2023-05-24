"""Composite Model."""
from dataclasses import dataclass
from typing import Collection, Dict, List, Optional, Sequence, cast

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion, Operator, UnitSystem
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .data_sources import (
    CompositeDataSources,
    ContinuousFiberCompositesFiles,
    get_composites_data_sources,
)
from .failure_criteria import CombinedFailureCriterion
from .layup_info import (
    ElementInfo,
    LayerProperty,
    LayupPropertiesProvider,
    add_layup_info_to_mesh,
    get_element_info_provider,
)
from .layup_info.material_operators import MaterialOperators, get_material_operators
from .layup_info.material_properties import MaterialProperty, get_constant_property_dict
from .result_definition import FailureMeasure, ResultDefinition, ResultDefinitionScope
from .sampling_point import SamplingPoint
from .server_helpers import upload_continuous_fiber_composite_files_to_server
from .unit_system import UnitSystemProvider, get_unit_system

__all__ = ("CompositeScope", "CompositeInfo", "CompositeModel")


@dataclass(frozen=True)
class CompositeScope:
    """Provides the composite scope.

    This class defines which part of the model and solution step are selected.

    Parameters
    ----------
    elements:
        List of elements.
    plies:
        List of plies.
    time:
        Time or frequency. You can use the
        :func:`CompositeModel.get_result_times_or_frequencies` method
        to list the solution steps.
    named_selections:
        List of element sets.
        Use `composite_model.get_mesh().available_named_selections` to list
        all named selections.

    Notes
    -----
    If more than one scope (``elements``, ``named_selections`` and ``plies``)
    is set, then the final element scope is the intersection
    of the defined parameters. All elements are selected if no parameter is set.

    """

    elements: Optional[Sequence[int]] = None
    plies: Optional[Sequence[str]] = None
    time: Optional[float] = None
    named_selections: Optional[Sequence[str]] = None


class CompositeInfo:
    """Contains composite data providers for a composite definition."""

    def __init__(
        self,
        data_sources: CompositeDataSources,
        composite_definition_label: str,
        streams_provider: dpf.Operator,
        material_operators: MaterialOperators,
        unit_system: UnitSystemProvider,
    ):
        """Initialize ``CompositeInfo`` class and add enriched mesh with composite information."""
        mesh_provider = dpf.Operator("MeshProvider")
        mesh_provider.inputs.data_sources(data_sources.rst)
        self.mesh = mesh_provider.outputs.mesh()

        self.layup_provider = add_layup_info_to_mesh(
            mesh=self.mesh,
            data_sources=data_sources,
            material_operators=material_operators,
            unit_system=unit_system,
            composite_definition_label=composite_definition_label,
        )

        self.element_info_provider = get_element_info_provider(
            mesh=self.mesh,
            stream_provider_or_data_source=streams_provider,
        )
        self.layup_properties_provider = LayupPropertiesProvider(
            layup_provider=self.layup_provider, mesh=self.mesh
        )


class CompositeModel:
    """Provides access to the basic composite postprocessing functionality.

    On initialization, the ``CompositeModel`` class automatically adds composite lay-up
    information to the meshed regions. It prepares the providers for different lay-up properties
    so that they can be efficiently evaluated. The composite_files provided are automatically
    uploaded to the server if needed.

    .. note::

        When creating a ``CompositeModel`` instance, several providers are created and
        lay-up information is added to the DPF meshed regions. Depending on the use
        case, it can be more efficient to create the providers separately.

        For assemblies with multiple composite definition files, separate meshes and
        lay-up operators are generated (wrapped by the ``CompositeInfo`` class). This
        is needed because the lay-up provider can currently only add the data of a single
        composite definitions file to a mesh. All functions that depend on composite
        definitions mut be called with the correct ``composite_definition_label``
        parameter. The layered elements that get information from a given
        composite definition label can be determined by calling
        ``self.get_all_layered_element_ids_for_composite_definition_label``.
        All the elements that are not part of a composite definition are either homogeneous
        solids or layered models defined outside of an ACP model. The
        ``self.composite_definition_labels`` command returns all available composite
        definition labels. For more information, see
        :ref:`sphx_glr_examples_gallery_examples_8_assembly_example.py`.

    Parameters
    ----------
    composite_files:
        Use the :func:`.get_composite_files_from_workbench_result_folder` function to obtain
        the :class:`.ContinuousFiberCompositesFiles` object.
    server:
        DPF Server on which the model is created
    default_unit_system:
        Unit system that is used if the result file
        does not specify the unit system. This happens
        for pure MAPDL projects.
    """

    def __init__(
        self,
        composite_files: ContinuousFiberCompositesFiles,
        server: BaseServer,
        default_unit_system: Optional[UnitSystem] = None,
    ):
        """Initialize data providers and add composite information to meshed region."""
        self._composite_files = upload_continuous_fiber_composite_files_to_server(
            composite_files, server
        )
        self._core_model = dpf.Model(self._composite_files.rst, server=server)
        self._server = server

        self._data_sources = get_composites_data_sources(self._composite_files)

        self._unit_system = get_unit_system(self._data_sources.rst, default_unit_system)

        self._material_operators = get_material_operators(
            rst_data_source=self._data_sources.rst,
            unit_system=self._unit_system,
            engineering_data_source=self._data_sources.engineering_data,
        )

        self._composite_infos: Dict[str, CompositeInfo] = {}
        for composite_definition_label in self._data_sources.composite:
            self._composite_infos[composite_definition_label] = CompositeInfo(
                self._data_sources,
                composite_definition_label,
                self._core_model.metadata.streams_provider,
                material_operators=self._material_operators,
                unit_system=self._unit_system,
            )

    @property
    def composite_definition_labels(self) -> Sequence[str]:
        """All composite definition labels in the model.

        This property is only relevant for assemblies.
        """
        return list(self._composite_infos.keys())

    @property
    def composite_files(self) -> ContinuousFiberCompositesFiles:
        """Get the composite file paths on the server."""
        return self._composite_files

    def get_mesh(self, composite_definition_label: Optional[str] = None) -> MeshedRegion:
        """Get the underlying DPF meshed region.

        The meshed region contains the lay-up information.

        Parameters
        ----------
        composite_definition_label :
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return self._composite_infos[composite_definition_label].mesh

    @property
    def data_sources(self) -> CompositeDataSources:
        """Composite data sources."""
        return self._data_sources

    @property
    def core_model(self) -> dpf.Model:
        """Underlying DPF core model."""
        return self._core_model

    @property
    def material_operators(self) -> MaterialOperators:
        """Material operators."""
        return self._material_operators

    def get_layup_operator(self, composite_definition_label: Optional[str] = None) -> Operator:
        """Get the lay-up operators.

        Parameters
        ----------
        composite_definition_label :
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.

        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return self._composite_infos[composite_definition_label].layup_provider

    def evaluate_failure_criteria(
        self,
        combined_criterion: CombinedFailureCriterion,
        composite_scope: Optional[CompositeScope] = None,
        measure: FailureMeasure = FailureMeasure.INVERSE_RESERVE_FACTOR,
        write_data_for_full_element_scope: bool = True,
    ) -> FieldsContainer:
        """Get a fields container with the evaluated failure criteria.

        The fields container contains the maximum per element if the measure
        is :attr:`.FailureMeasure.INVERSE_RESERVE_FACTOR` and the minimum per element
        if the measure is :attr:`.FailureMeasure.MARGIN_OF_SAFETY` or
        :attr:`.FailureMeasure.RESERVE_FACTOR`.

        Parameters
        ----------
        combined_criterion :
            Combined failure criterion to evaluate.
        composite_scope :
            Composite scope on which to evaluate the failure criteria. If empty, the criteria
            is evaluated on the full model. If the time is not set, the last time or
            frequency in the result file is used.
        measure :
            Failure measure to evaluate.
        write_data_for_full_element_scope :
            Whether each element in the element scope is to get a
            (potentially zero) failure value, even elements that are not
            part of ``composite_scope.plies``. If no element scope is
            specified (``composite_scope.elements``), a (potentially zero)
            failure value is written for all elements.

            .. note::

                For some special element types such as beams,
                ``write_data_for_full_element_scope=True`` is not supported.

        """
        if composite_scope is None:
            composite_scope = CompositeScope()

        element_scope_in = [] if composite_scope.elements is None else composite_scope.elements
        ply_scope_in = [] if composite_scope.plies is None else composite_scope.plies
        ns_in = [] if composite_scope.named_selections is None else composite_scope.named_selections
        time_in = composite_scope.time

        if composite_scope.plies is None or len(composite_scope.plies):
            # This is a workaround because setting the
            # write_data_for_full_element_scope flag to True can lead to
            # problems with 2023 R1 if non-composite elements such as
            # beams exist in the solution. Because the flag
            # is irrelevant for cases without a ply scope, we set it to False here.
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
                    named_selection_scope=ns_in,
                    write_data_for_full_element_scope=write_data_for_full_element_scope,
                )
            )

        rd = ResultDefinition(
            name="combined failure criteria",
            rst_file=self._composite_files.rst,
            material_file=self._composite_files.engineering_data,
            combined_failure_criterion=combined_criterion,
            composite_scopes=scopes,
            time=time_in,
            measure=measure.value,
        )
        failure_operator = dpf.Operator("composite::composite_failure_operator")

        failure_operator.inputs.result_definition(rd.to_json())

        if measure == FailureMeasure.INVERSE_RESERVE_FACTOR:
            return failure_operator.outputs.fields_containerMax()
        else:
            return failure_operator.outputs.fields_containerMin()

    def get_sampling_point(
        self,
        combined_criterion: CombinedFailureCriterion,
        element_id: int,
        time: Optional[float] = None,
        composite_definition_label: Optional[str] = None,
    ) -> SamplingPoint:
        """Get a sampling point for an element ID and failure criteria.

        Parameters
        ----------
        combined_criterion:
            Combined failure criterion to evaluate.
        element_id:
            Element ID or label of the sampling point.
        time:
            Time or frequency at which to evaluate the sampling point. If ``None``,
            the last time or frequency in the result file is used.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
        """
        time_in = time

        if composite_definition_label is None:
            # jvonrick: Jan 2023: We could also try to determine composite_definition_label
            # based on the element_id and
            # self.get_all_layered_element_ids_for_composite_definition_label.
            # But the element_id of the sampling point can be changed later
            # In this case it is complicated switch to the correct composite definition, so
            # it is probably better to make it explicit that the sampling point is tied to
            # a composite definition
            composite_definition_label = self._first_composite_definition_label_if_only_one()

        scope = ResultDefinitionScope(
            composite_definition=self._composite_files.composite[
                composite_definition_label
            ].definition,
            mapping_file=self._composite_files.composite[composite_definition_label].mapping,
            element_scope=[element_id],
            ply_scope=[],
            named_selection_scope=[],
        )
        rd = ResultDefinition(
            name="combined failure criteria",
            rst_file=self._composite_files.rst,
            material_file=self._composite_files.engineering_data,
            combined_failure_criterion=combined_criterion,
            time=time_in,
            composite_scopes=[scope],
        )

        return SamplingPoint("Sampling Point", rd, server=self._server)

    def get_element_info(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[ElementInfo]:
        """Get element information for an element ID.

        This method returns ``None`` if the element type is not supported.

        Parameters
        ----------
        element_id:
            Element ID or label.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
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
        """Get a layer property for an element ID.

        Returns a numpy array with the values of the property for all the layers.
        Values are ordered from bottom to top.

        This method returns ``None`` if the element is not layered.

        Parameters
        ----------
        layup_property:
            Lay-up property.
        element_id:
            Element ID or label.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        layup_properties_provider = self._composite_infos[
            composite_definition_label
        ].layup_properties_provider
        if layup_property == LayerProperty.ANGLES:
            return layup_properties_provider.get_layer_angles(element_id)
        if layup_property == LayerProperty.THICKNESSES:
            return layup_properties_provider.get_layer_thicknesses(element_id)
        if layup_property == LayerProperty.SHEAR_ANGLES:
            return layup_properties_provider.get_layer_shear_angles(element_id)
        raise RuntimeError(f"Invalid property {layup_property}")

    def get_analysis_plies(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[Collection[str]]:
        """Get analysis ply names.

        This method returns ``None`` if the element is not layered.

        Parameters
        ----------
        element_id:
            Element ID or label.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
            The dictionary only contains the analysis plies in the specified composite
            definition.
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
        """Get the laminate offset of an element.

        THis method returns ``None`` if the element is not layered.

        Parameters
        ----------
        element_id:
            Element ID or label.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
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

        Returns a dictionary with ``dpf_material_id`` as the key and
        a dictionary with the requested properties as the value. Only constant properties
        are supported. Variable properties are evaluated at their
        default values.

        This method can be slow to evaluate and should not
        be called in a loop.

        Parameters
        ----------
        material_properties:
            List of the requested material properties.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
            The dictionary only contains the materials of the analysis plies defined
            in the specified composite definition.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()
        return get_constant_property_dict(
            material_properties=material_properties,
            materials_provider=self.material_operators.material_provider,
            data_source_or_streams_provider=self.core_model.metadata.streams_provider,
            mesh=self.get_mesh(composite_definition_label),
        )

    def get_result_times_or_frequencies(self) -> NDArray[np.double]:
        """Get the times or frequencies in the result file."""
        return cast(
            NDArray[np.double], self._core_model.metadata.time_freq_support.time_frequencies.data
        )

    def add_interlaminar_normal_stresses(
        self,
        stresses: FieldsContainer,
        strains: FieldsContainer,
        composite_definition_label: Optional[str] = None,
    ) -> None:
        """Add interlaminar normal stresses to the stresses fields container.

        For a usage example, see
        :ref:`sphx_glr_examples_gallery_examples_7_interlaminar_normal_stress_example.py`.

        Parameters
        ----------
        stresses:
            Stresses fields container to add interlaminar normal stresses to.
        strains:
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
            Interlaminar normal stresses are only added to the layered elements defined
            in the specified composite definition.
        """
        if composite_definition_label is None:
            composite_definition_label = self._first_composite_definition_label_if_only_one()

        layup_provider = self._composite_infos[composite_definition_label].layup_provider
        ins_operator = dpf.Operator("composite::interlaminar_normal_stress_operator")
        ins_operator.inputs.materials_container(self._material_operators.material_provider)
        ins_operator.inputs.mesh(self.get_mesh(composite_definition_label))
        ins_operator.inputs.mesh_properties_container(
            layup_provider.outputs.mesh_properties_container
        )
        ins_operator.inputs.section_data_container(layup_provider.outputs.section_data_container)
        ins_operator.inputs.strains_container(strains)
        ins_operator.inputs.stresses_container(stresses)

        # call run because ins operator has not output
        ins_operator.run()

    def get_all_layered_element_ids_for_composite_definition_label(
        self, composite_definition_label: str
    ) -> Sequence[int]:
        """Get all layered element IDs that belong to a composite definition label.

        Parameters
        ----------
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
        """
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
                f"Multiple composite definition keys exist: {self.composite_definition_labels}. "
                f"Specify a key explicitly."
            )
