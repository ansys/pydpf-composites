# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Composite Model Interface."""
# New interface after 2023 R2
from collections.abc import Collection, Sequence
from typing import Any, Callable, Optional, cast
from warnings import warn

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion, Operator, UnitSystem
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .composite_scope import CompositeScope
from .constants import FAILURE_LABEL, REF_SURFACE_NAME, TIME_LABEL, FailureOutput
from .data_sources import (
    CompositeDataSources,
    ContinuousFiberCompositesFiles,
    get_composites_data_sources,
)
from .failure_criteria import CombinedFailureCriterion
from .layup_info import (
    ElementInfo,
    LayerProperty,
    LayupModelContextType,
    LayupPropertiesProvider,
    add_layup_info_to_mesh,
    get_element_info_provider,
)
from .layup_info._layup_info import _get_layup_model_context
from .layup_info._reference_surface import (
    _get_map_to_reference_surface_operator,
    _get_reference_surface_and_mapping_field,
)
from .layup_info.material_operators import MaterialOperators, get_material_operators
from .layup_info.material_properties import MaterialProperty, get_constant_property_dict
from .result_definition import FailureMeasureEnum
from .sampling_point import SamplingPointNew
from .server_helpers import (
    upload_continuous_fiber_composite_files_to_server,
    version_equal_or_later,
)
from .unit_system import get_unit_system


def _deprecated_composite_definition_label(func: Callable[..., Any]) -> Any:
    """Emit a warning when the deprecated ``composite_definition_label`` is used."""
    function_arg = "composite_definition_label"

    def inner(*args: Sequence[Any], **kwargs: Sequence[Any]) -> Any:
        if function_arg in kwargs.keys():
            if kwargs[function_arg]:
                warn(
                    f"Use of {function_arg} is deprecated. Function {func.__name__}."
                    " can be called without this argument.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
        return func(*args, **kwargs)

    return inner


def _merge_containers(
    non_ref_surface_container: FieldsContainer, ref_surface_container: FieldsContainer
) -> FieldsContainer:
    """
    Merge the results fields container.

    Merges the results fields container of the non-reference surface and the reference surface.
    """
    assert sorted(non_ref_surface_container.labels) == sorted(ref_surface_container.labels)

    ref_surface_time_ids = ref_surface_container.get_available_ids_for_label(TIME_LABEL)
    non_ref_surface_time_ids = non_ref_surface_container.get_available_ids_for_label(TIME_LABEL)

    assert sorted(ref_surface_time_ids) == sorted(non_ref_surface_time_ids)

    out_container = dpf.FieldsContainer()
    out_container.labels = [TIME_LABEL, FAILURE_LABEL]
    out_container.time_freq_support = non_ref_surface_container.time_freq_support

    def add_to_output_container(time_id: int, source_container: FieldsContainer) -> None:
        fields = source_container.get_fields({TIME_LABEL: time_id})
        for field in fields:
            failure_enum = _get_failure_enum_from_name(field.name)
            out_container.add_field({TIME_LABEL: time_id, FAILURE_LABEL: failure_enum}, field)

    for current_time_id in ref_surface_time_ids:
        add_to_output_container(current_time_id, ref_surface_container)
        add_to_output_container(current_time_id, non_ref_surface_container)

    return out_container


def _get_failure_enum_from_name(name: str) -> FailureOutput:
    if name.startswith("Failure Mode"):
        if name.endswith(REF_SURFACE_NAME):
            return FailureOutput.FAILURE_MODE_REF_SURFACE
        else:
            return FailureOutput.FAILURE_MODE

    if name.startswith("IRF") or name.startswith("SF") or name.startswith("SM"):
        if name.endswith(REF_SURFACE_NAME):
            return FailureOutput.FAILURE_VALUE_REF_SURFACE
        else:
            return FailureOutput.FAILURE_VALUE

    if name.startswith("Layer Index"):
        return FailureOutput.MAX_LAYER_INDEX

    if name.startswith("Global Layer in Stack"):
        return FailureOutput.MAX_GLOBAL_LAYER_IN_STACK

    if name.startswith("Local Layer in Element"):
        return FailureOutput.MAX_LOCAL_LAYER_IN_ELEMENT

    if name.startswith("Solid Element Id"):
        return FailureOutput.MAX_SOLID_ELEMENT_ID

    raise RuntimeError("Could not determine failure output from name: " + name)


class CompositeModelImpl:
    """Provides access to the basic composite postprocessing functionality.

    This class supports DPF Server version 7.0 (2024 R1) and later.
    On initialization, the ``CompositeModel`` class automatically adds composite lay-up
    information to the meshed regions. It prepares the providers for different lay-up properties
    so that they can be efficiently evaluated. The composite files provided are automatically
    uploaded to the server if needed.

    .. note::

        When creating a ``CompositeModel`` instance, several providers are created and
        lay-up information is added to the DPF meshed regions. Depending on the use
        case, it can be more efficient to create the providers separately.

    Parameters
    ----------
    composite_files:
        Use the :func:`.get_composite_files_from_workbench_result_folder` function to obtain
        the :class:`.ContinuousFiberCompositesFiles` object.
    server:
        DPF Server to create the model on.
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
            rst_stream_provider=self._get_rst_streams_provider(),
        )

        # self._layup_provider.outputs.layup_model_context_type.get_data() does not work because
        # int32 is not supported in the Python API. See bug 946754.
        if version_equal_or_later(self._server, "8.0"):
            self._layup_model_type = LayupModelContextType(
                _get_layup_model_context(self._layup_provider)
            )
        else:
            self._layup_model_type = (
                LayupModelContextType.ACP
                if len(composite_files.composite) > 0
                else LayupModelContextType.NOT_AVAILABLE
            )

        if self._supports_reference_surface_operators():
            self._reference_surface_and_mapping_field = _get_reference_surface_and_mapping_field(
                data_sources=self.data_sources.composite, unit_system=self._unit_system
            )

            self._map_to_reference_surface_operator = _get_map_to_reference_surface_operator(
                reference_surface_and_mapping_field=self._reference_surface_and_mapping_field,
                element_layer_indices_field=self.get_mesh().property_field("element_layer_indices"),
            )

        self._element_info_provider = get_element_info_provider(
            mesh=self.get_mesh(),
            stream_provider_or_data_source=self._get_rst_streams_provider(),
            material_provider=self.material_operators.material_provider,
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
        """Composite file paths on the server."""
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

    @property
    def material_names(self) -> dict[str, int]:
        """
        Material name to DPF material ID map.

        This property can be used to filter analysis plies
        or element layers.
        """
        try:
            helper_op = dpf.Operator("composite::materials_container_helper")
        except Exception as exc:
            raise RuntimeError(
                f"Operator composite::materials_container_helper doesn't exist. "
                f"This could be because the server version is 2024 R1-pre0. The "
                f"latest preview or the unified installer can be used instead. "
                f"Error: {exc}"
            ) from exc

        helper_op.inputs.materials_container(self._material_operators.material_provider.outputs)
        string_field = helper_op.outputs.material_names()
        material_ids = string_field.scoping.ids

        names = {}
        for dpf_mat_id in material_ids:
            names[string_field.data[string_field.scoping.index(dpf_mat_id)]] = dpf_mat_id

        return names

    @_deprecated_composite_definition_label
    def get_mesh(self, composite_definition_label: Optional[str] = None) -> MeshedRegion:
        """Get the underlying DPF meshed region.

        The meshed region contains the lay-up information.
        """
        return self._core_model.metadata.meshed_region

    @_deprecated_composite_definition_label
    def get_layup_operator(self, composite_definition_label: Optional[str] = None) -> Operator:
        """Get the lay-up operator.

        Parameters
        ----------
        composite_definition_label :
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.

        """
        return self._layup_provider

    @property
    def layup_model_type(self) -> LayupModelContextType:
        """Get the context type of the lay-up model.

        Type can be one of the following values: ``NOT_AVAILABLE``, ``ACP``, ``RST``, ``MIXED``.
        """
        return self._layup_model_type

    @_deprecated_composite_definition_label
    def evaluate_failure_criteria(
        self,
        combined_criterion: CombinedFailureCriterion,
        composite_scope: Optional[CompositeScope] = None,
        measure: FailureMeasureEnum = FailureMeasureEnum.INVERSE_RESERVE_FACTOR,
        write_data_for_full_element_scope: bool = True,
        max_chunk_size: int = 50000,
    ) -> FieldsContainer:
        """Get a fields container with the evaluated failure criteria.

        The fields container contains the maximum per element if the measure
        is :attr:`.FailureMeasureEnum.INVERSE_RESERVE_FACTOR` and the minimum per element
        if the measure is the :attr:`.FailureMeasureEnum.MARGIN_OF_SAFETY` or
        :attr:`.FailureMeasureEnum.RESERVE_FACTOR` attribute.

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
        max_chunk_size:
            Maximum chunk size. If number of elements is larger than this number,
            the failure criteria are evaluated in chunks of the specified size.

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

        # configure primary scoping
        scope_config = dpf.DataTree()
        if time_in:
            scope_config.add({"requested_times": time_in})
        scope_config_reader_op = dpf.Operator("composite::scope_config_reader")
        scope_config_reader_op.inputs.scope_configuration(scope_config)

        if ply_scope_in:
            selected_plies_op = dpf.Operator("composite::string_container")
            for value in enumerate(ply_scope_in):
                selected_plies_op.connect(value[0], value[1])
            scope_config_reader_op.inputs.ply_ids(selected_plies_op.outputs.strings)

        # configure operator to chunk the scope
        chunking_data_tree = dpf.DataTree({"max_chunk_size": max_chunk_size})
        if ns_in:
            chunking_data_tree.add({"named_selections": ns_in})

        chunking_generator = dpf.Operator("composite::scope_generator")
        chunking_generator.inputs.stream_provider(self._get_rst_streams_provider())
        chunking_generator.inputs.data_tree(chunking_data_tree)
        if self.data_sources.composite:
            chunking_generator.inputs.data_sources(self.data_sources.composite)

        if element_scope_in:
            element_scope = dpf.Scoping(location="elemental")
            element_scope.ids = element_scope_in
            chunking_generator.inputs.element_scoping(element_scope)

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

            # Live evaluation is currently not supported by the Python module
            # because the docker container does not support it.
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
                self._get_rst_streams_provider()
            )
            evaluate_failure_criterion_per_scope_op.inputs.mesh(self.get_mesh())
            if version_equal_or_later(self._server, "8.0"):
                evaluate_failure_criterion_per_scope_op.inputs.layup_model_context_type(
                    self.layup_model_type.value
                )
            else:
                evaluate_failure_criterion_per_scope_op.inputs.has_layup_provider(
                    self.layup_model_type != LayupModelContextType.NOT_AVAILABLE
                )
            evaluate_failure_criterion_per_scope_op.inputs.section_data_container(
                self._layup_provider.outputs.section_data_container
            )
            evaluate_failure_criterion_per_scope_op.inputs.material_fields(
                self._layup_provider.outputs.material_fields
            )
            evaluate_failure_criterion_per_scope_op.inputs.mesh_properties_container(
                self._layup_provider.outputs.mesh_properties_container
            )
            # Ensure that sandwich criteria are evaluated
            evaluate_failure_criterion_per_scope_op.inputs.request_sandwich_results(True)

            # Note: the min/max layer indices are 1-based starting with
            # Workbench 2024 R1 (DPF server 7.1)
            minmax_el_op = dpf.Operator("composite::minmax_per_element_operator")
            minmax_el_op.inputs.fields_container(
                evaluate_failure_criterion_per_scope_op.outputs.failure_container
            )

            minmax_el_op.inputs.mesh(self.get_mesh())
            minmax_el_op.inputs.material_support(
                self.material_operators.material_support_provider.outputs
            )

            if (
                self.layup_model_type != LayupModelContextType.NOT_AVAILABLE
                and write_data_for_full_element_scope
            ):
                add_default_data_op = dpf.Operator("composite::add_default_data")
                add_default_data_op.inputs.requested_element_scoping(chunking_generator.outputs)
                add_default_data_op.inputs.time_id(
                    evaluate_failure_criterion_per_scope_op.outputs.time_id
                )

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
            converter_op.inputs.measure_type(measure.value)
            converter_op.run()

            converter_op.inputs.fields_container(max_container)
            converter_op.run()

            min_merger.connect(merge_index, min_container)
            max_merger.connect(merge_index, max_container)
            merge_index = merge_index + 1

        if merge_index == 0:
            raise RuntimeError("No output is generated! Check the scope (element and ply IDs).")

        if self._supports_reference_surface_operators():
            self._map_to_reference_surface_operator.inputs.min_container(
                min_merger.outputs.merged_fields_container()
            )
            self._map_to_reference_surface_operator.inputs.max_container(
                max_merger.outputs.merged_fields_container()
            )

            if measure == FailureMeasureEnum.INVERSE_RESERVE_FACTOR:
                return _merge_containers(
                    max_merger.outputs.merged_fields_container(),
                    self._map_to_reference_surface_operator.outputs.max_container(),
                )
            else:
                return _merge_containers(
                    min_merger.outputs.merged_fields_container(),
                    self._map_to_reference_surface_operator.outputs.min_container(),
                )
        else:
            if measure == FailureMeasureEnum.INVERSE_RESERVE_FACTOR:
                return max_merger.outputs.merged_fields_container()
            else:
                return min_merger.outputs.merged_fields_container()

    @_deprecated_composite_definition_label
    def get_sampling_point(
        self,
        combined_criterion: CombinedFailureCriterion,
        element_id: int,
        time: Optional[float] = None,
        composite_definition_label: Optional[str] = None,
    ) -> SamplingPointNew:
        """Get a sampling point for an element ID and failure criteria.

        Parameters
        ----------
        combined_criterion:
            Combined failure criterion to evaluate.
        element_id:
            Element ID or label of the sampling point.
        time:
            Time or frequency to evaluate the sampling point at. The default
            is ``None``, in which case the last time or frequency in the result
            file is used.
        composite_definition_label:
            Label of the composite definition, which is the
            dictionary key in the :attr:`.ContinuousFiberCompositesFiles.composite`
            attribute. This parameter is only required for assemblies.
            See the note about assemblies in the description for the :class:`CompositeModel` class.
        """
        time_in = time

        return SamplingPointNew(
            "Sampling Point",
            element_id,
            combined_criterion,
            self._material_operators,
            self.get_mesh(),
            self._layup_provider,
            self._get_rst_streams_provider(),
            self._data_sources.rst,
            self._unit_system,
            time_in,
        )

    @_deprecated_composite_definition_label
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

    @_deprecated_composite_definition_label
    def get_property_for_all_layers(
        self,
        layup_property: LayerProperty,
        element_id: int,
        composite_definition_label: Optional[str] = None,
    ) -> Optional[NDArray[np.double]]:
        """Get a layer property for an element ID.

        This method returns a numpy array with the values of the property for all the layers.
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

    @_deprecated_composite_definition_label
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

    @_deprecated_composite_definition_label
    def get_element_laminate_offset(
        self, element_id: int, composite_definition_label: Optional[str] = None
    ) -> Optional[np.double]:
        """Get the laminate offset of an element.

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
        """
        return self._layup_properties_provider.get_element_laminate_offset(element_id)

    @_deprecated_composite_definition_label
    def get_constant_property_dict(
        self,
        material_properties: Collection[MaterialProperty],
        composite_definition_label: Optional[str] = None,
    ) -> dict[np.int64, dict[MaterialProperty, float]]:
        """Get a dictionary with constant properties.

        This method returns a dictionary with ``dpf_material_id`` as the key and
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
            data_source_or_streams_provider=self._get_rst_streams_provider(),
            mesh=self.get_mesh(),
        )

    def get_result_times_or_frequencies(self) -> NDArray[np.double]:
        """Get the times or frequencies in the result file."""
        return cast(
            NDArray[np.double], self._core_model.metadata.time_freq_support.time_frequencies.data
        )

    @_deprecated_composite_definition_label
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
            Strains fields container from which the interlaminar normal stresses
            are computed.

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

    def get_all_layered_element_ids(self) -> Sequence[int]:
        """Get all layered element IDs."""
        return cast(
            list[int],
            self.get_mesh().property_field("element_layer_indices").scoping.ids,
        )

    def get_all_layered_element_ids_for_composite_definition_label(
        self, composite_definition_label: Optional[str] = None
    ) -> Sequence[int]:
        """Get all layered element IDs that belong to a composite definition label.

        Parameters
        ----------
        composite_definition_label:
            Deprecated. This parameter is no longer needed.
        """
        warn(
            "The get_all_layered_element_ids_for_composite_definition_label method is deprecated. "
            "Use the get_all_layered_element_ids method instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.get_all_layered_element_ids()

    def _get_rst_streams_provider(self) -> Operator:
        return self._core_model.metadata.streams_provider

    def _first_composite_definition_label_if_only_one(self) -> str:
        if len(self.composite_definition_labels) == 1:
            return self.composite_definition_labels[0]
        else:
            raise RuntimeError(
                f"Multiple composite definition keys exist: {self.composite_definition_labels}. "
                f"Specify a key explicitly."
            )

    # Whether the reference surface operators are available or supported by the server
    def _supports_reference_surface_operators(self) -> bool:
        if not version_equal_or_later(self._server, "8.0"):
            return False

        if (
            self.layup_model_type == LayupModelContextType.ACP
            or self.layup_model_type == LayupModelContextType.MIXED
        ):
            return True

        return False
