"""Composite Model Interface."""
# New interface after 2023 R2
from typing import Collection, Dict, List, Optional, Sequence, Union, cast

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion, Operator, UnitSystem
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .composite_scope import CompositeScope
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
from .result_definition import FailureMeasureEnum
from .sampling_point import SamplingPoint
from .server_helpers import upload_continuous_fiber_composite_files_to_server
from .unit_system import get_unit_system


class CompositeModelInterface:
    """Provides access to the basic composite postprocessing functionality.

    This interface supports DPF server version 7.0 and later.
    On initialization, the ``CompositeModel`` class automatically adds composite lay-up
    information to the meshed regions. It prepares the providers for different lay-up properties
    so that they can be efficiently evaluated. The composite_files provided are automatically
    uploaded to the server if needed.

    .. note::

        When creating a ``CompositeModel`` instance, several providers are created and
        lay-up information is added to the DPF meshed regions. Depending on the use
        case, it can be more efficient to create the providers separately.

        Assemblies are now fully supported and so the handling is much easier if
        compared with previous versions of the backend.

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
        self._data_sources = get_composites_data_sources(self._composite_files)

        self._core_model = dpf.Model(self._data_sources.rst, server=server)
        self._server = server

        self._unit_system = get_unit_system(self._data_sources.rst, default_unit_system)

        self._material_operators = get_material_operators(
            rst_data_source=self._data_sources.material_support,
            unit_system=self._unit_system,
            engineering_data_source=self._data_sources.engineering_data,
        )

        self._layup_provider = add_layup_info_to_mesh(
            mesh=self.get_mesh(),
            data_sources=self.data_sources,
            material_operators=self.material_operators,
            unit_system=self._unit_system,
        )

        self._element_info_provider = get_element_info_provider(
            mesh=self.get_mesh(),
            stream_provider_or_data_source=self._stream_provider(),
        )
        self._layup_properties_provider = LayupPropertiesProvider(
            layup_provider=self._layup_provider, mesh=self.get_mesh()
        )

    @property
    def composite_definition_labels(self) -> Sequence[str]:
        """All composite definition labels in the model.

        This property is only relevant for assemblies to access
        plies by ID.
        """
        return list(self.composite_files.composite.keys())

    @property
    def composite_files(self) -> ContinuousFiberCompositesFiles:
        """Get the composite file paths on the server."""
        return self._composite_files

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

    def get_mesh(self, composite_definition_label: Optional[str] = None) -> MeshedRegion:
        """Get the underlying DPF meshed region.

        The meshed region contains the lay-up information.
        """
        return self._core_model.metadata.meshed_region

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
        return self._layup_provider

    def evaluate_failure_criteria(
        self,
        combined_criterion: CombinedFailureCriterion,
        composite_scope: Optional[CompositeScope] = None,
        measure: FailureMeasureEnum = FailureMeasureEnum.INVERSE_RESERVE_FACTOR,
        write_data_for_full_element_scope: bool = True,
    ) -> FieldsContainer:
        """Get a fields container with the evaluated failure criteria.

        The fields container contains the maximum per element if the measure
        is :attr:`.FailureMeasureEnum.INVERSE_RESERVE_FACTOR` and the minimum per element
        if the measure is :attr:`.FailureMeasureEnum.MARGIN_OF_SAFETY` or
        :attr:`.FailureMeasureEnum.RESERVE_FACTOR`.

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

        # todo: how to pass the time ids and ply_scope
        element_scope_in = [] if composite_scope.elements is None else composite_scope.elements
        # ply_scope_in = [] if composite_scope.plies is None else composite_scope.plies
        ns_in = [] if composite_scope.named_selections is None else composite_scope.named_selections
        # time_in = composite_scope.time

        if composite_scope.plies is None or len(composite_scope.plies):
            # This is a workaround because setting the
            # write_data_for_full_element_scope flag to True can lead to
            # problems with 2023 R1 if non-composite elements such as
            # beams exist in the solution. Because the flag
            # is irrelevant for cases without a ply scope, we set it to False here.
            write_data_for_full_element_scope = False

        has_layup_provider = len(self._composite_files.composite) > 0

        scope_config_reader_op = dpf.Operator("composite::scope_config_reader")
        scope_config_reader_op.inputs.write_data_for_full_element_scope(
            write_data_for_full_element_scope
        )
        # todo: set time ids and ply ids via DataTree

        chunking_config: Dict[str, Union[int, Sequence[str]]] = {"max_chunk_size": 50000}
        if ns_in:
            chunking_config["named_selections"] = ns_in

        chunking_data_tree = dpf.DataTree(chunking_config)
        chunking_generator = dpf.Operator("composite::scope_generator")
        chunking_generator.inputs.stream_provider(self._stream_provider())
        chunking_generator.inputs.data_tree(chunking_data_tree)
        chunking_generator.inputs.data_sources(self.data_sources.composite)
        if element_scope_in:
            element_scoping = dpf.Scoping()
            element_scoping.ids = element_scope_in
            chunking_generator.inputs.element_scoping(element_scoping)

        min_merger = dpf.Operator("merge::fields_container")
        max_merger = dpf.Operator("merge::fields_container")

        merge_index = 0

        while True:
            chunking_generator.inputs.generator_counter(merge_index)
            finished = chunking_generator.outputs.is_finished()
            if finished:
                break

            evaluate_failure_criterion_per_scope_op = dpf.Operator(
                "composite::evaluate_failure_criterion_per_scope"
            )

            # Todo: live evaluation flag missing
            evaluate_failure_criterion_per_scope_op.inputs.criterion_configuration(
                combined_criterion.to_json()
            )

            evaluate_failure_criterion_per_scope_op.inputs.scope_configuration(
                scope_config_reader_op.outputs
            )

            evaluate_failure_criterion_per_scope_op.inputs.element_scoping(
                chunking_generator.outputs
            )
            evaluate_failure_criterion_per_scope_op.inputs.materials_container(
                self.material_operators.material_provider.outputs
            )
            evaluate_failure_criterion_per_scope_op.inputs.stream_provider(
                self._stream_provider().outputs
            )
            evaluate_failure_criterion_per_scope_op.inputs.mesh(self.get_mesh())
            evaluate_failure_criterion_per_scope_op.inputs.has_layup_provider(has_layup_provider)
            evaluate_failure_criterion_per_scope_op.inputs.section_data_container(
                self._layup_provider.outputs.section_data_container
            )
            evaluate_failure_criterion_per_scope_op.inputs.material_fields(
                self._layup_provider.outputs.material_fields
            )
            evaluate_failure_criterion_per_scope_op.inputs.mesh_properties_container(
                self._layup_provider.outputs.mesh_properties_container
            )
            # always set to true to ensure that solid stacks are grouped
            evaluate_failure_criterion_per_scope_op.inputs.request_sandwich_results(True)

            minmax_el_op = dpf.Operator("composite::minmax_per_element_operator")
            minmax_el_op.inputs.fields_container(
                evaluate_failure_criterion_per_scope_op.outputs.failure_container
            )
            # check if that is correct
            minmax_el_op.inputs.mesh(self.get_mesh())
            minmax_el_op.inputs.material_support(
                self.material_operators.material_support_provider.outputs
            )

            if has_layup_provider:
                add_default_data_op = dpf.Operator("composite::add_default_data")
                add_default_data_op.inputs.requested_element_scoping(chunking_generator.outputs)
                add_default_data_op.inputs.time_id(
                    evaluate_failure_criterion_per_scope_op.outputs.time_id
                )
                # check if that is correct
                add_default_data_op.inputs.mesh(self.get_mesh())

                add_default_data_op.inputs.fields_container(minmax_el_op.outputs.field_min)
                add_default_data_op.run()

                add_default_data_op.inputs.fields_container(minmax_el_op.outputs.field_max)
                add_default_data_op.run()

            # It is important to evaluate the field here, otherwise the merge operator detects
            # the workflow as changed if upstream operator inputs change
            min_container = minmax_el_op.outputs.field_min()
            max_container = minmax_el_op.outputs.field_max()

            converter_op = dpf.Operator("composite::failure_measure_converter")
            converter_op.inputs.fields_container(min_container)
            converter_op.inputs.measure_type(measure)
            converter_op.run()

            converter_op.inputs.fields_container(max_container)
            converter_op.run()

            min_merger.connect(merge_index, min_container)
            max_merger.connect(merge_index, max_container)
            merge_index = merge_index + 1

        if merge_index == 0:
            raise RuntimeError(
                "No output is generated! Please check the scope (element and ply ids)."
            )

        if measure == FailureMeasureEnum.INVERSE_RESERVE_FACTOR:
            return max_merger.outputs.merged_fields_container()
        else:
            return min_merger.outputs.merged_fields_container()

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

        return SamplingPoint("Sampling Point", element_id, time_in, combined_criterion)

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
        return self._element_info_provider.get_element_info(element_id)

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
        if layup_property == LayerProperty.ANGLES:
            return self._layup_properties_provider.get_layer_angles(element_id)
        if layup_property == LayerProperty.THICKNESSES:
            return self._layup_properties_provider.get_layer_thicknesses(element_id)
        if layup_property == LayerProperty.SHEAR_ANGLES:
            return self._layup_properties_provider.get_layer_shear_angles(element_id)
        raise RuntimeError(f"Invalid property {layup_property}")

    def get_analysis_plies(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[Sequence[str]]:
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
        return self._layup_properties_provider.get_analysis_plies(element_id)

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
        return self._layup_properties_provider.get_element_laminate_offset(element_id)

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
        return get_constant_property_dict(
            material_properties=material_properties,
            materials_provider=self.material_operators.material_provider,
            data_source_or_streams_provider=self._stream_provider(),
            mesh=self.get_mesh(),
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
        :ref:`sphx_glr_examples_gallery_examples_007_interlaminar_normal_stress_example.py`.

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
        ins_operator = dpf.Operator("composite::interlaminar_normal_stress_operator")
        ins_operator.inputs.materials_container(self._material_operators.material_provider)
        ins_operator.inputs.mesh(self.get_mesh())
        ins_operator.inputs.mesh_properties_container(
            self._layup_provider.outputs.mesh_properties_container
        )
        ins_operator.inputs.section_data_container(
            self._layup_provider.outputs.section_data_container
        )
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
            self.get_mesh().property_field("element_layer_indices").scoping.ids,
        )

    def _stream_provider(self) -> Operator:
        return self._core_model.metadata.streams_provider

    def _first_composite_definition_label_if_only_one(self) -> str:
        if len(self.composite_definition_labels) == 1:
            return self.composite_definition_labels[0]
        else:
            raise RuntimeError(
                f"Multiple composite definition keys exist: {self.composite_definition_labels}. "
                f"Specify a key explicitly."
            )
