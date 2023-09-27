"""Composite Model."""
from typing import Collection, Dict, Optional, Sequence

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion, Operator, UnitSystem
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from ._composite_model_factory import _composite_model_factory
from .composite_scope import CompositeScope
from .data_sources import CompositeDataSources, ContinuousFiberCompositesFiles
from .failure_criteria import CombinedFailureCriterion
from .layup_info import ElementInfo, LayerProperty
from .layup_info.material_operators import MaterialOperators
from .layup_info.material_properties import MaterialProperty
from .result_definition import FailureMeasureEnum
from .sampling_point_types import SamplingPoint


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

        The handling of models with multiple composite definition files (assemblies)
        differ depending on the version of the DPF server. The handling is simplified
        with DPF Server 7.0 (2024 R1) or later and the full assembly can be post-processed
        in the same way as a model with a single ACP model.

        Before DPF Server 7.0 (2024 R1):

        For assemblies with multiple composite definition files, separate meshes and
        lay-up operators are generated (wrapped by the ``CompositeInfo`` class). This
        is needed because the lay-up provider can only add the data of a single
        composite definitions file to a mesh. All functions that depend on composite
        definitions mut be called with the correct ``composite_definition_label``
        parameter. The layered elements that get information from a given
        composite definition label can be determined by calling
        :meth:`.CompositeModel.get_all_layered_element_ids_for_composite_definition_label`.
        All the elements that are not part of a composite definition are either homogeneous
        solids or layered models defined outside of an ACP model. The
        :meth:`.CompositeModel.composite_definition_labels` command returns all available composite
        definition labels. For more information, see
        :ref:`sphx_glr_examples_gallery_examples_008_assembly_example.py`.


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
        """Initialize the composite model class."""
        self._implementation = _composite_model_factory(server)(
            composite_files, server, default_unit_system
        )

    @property
    def composite_definition_labels(self) -> Sequence[str]:
        """All composite definition labels in the model.

        This property is only relevant for assemblies.
        """
        return self._implementation.composite_definition_labels

    @property
    def composite_files(self) -> ContinuousFiberCompositesFiles:
        """Get the composite file paths on the server."""
        return self._implementation.composite_files

    @property
    def data_sources(self) -> CompositeDataSources:
        """Composite data sources."""
        return self._implementation.data_sources

    @property
    def core_model(self) -> dpf.Model:
        """Underlying DPF core model."""
        return self._implementation.core_model

    @property
    def material_operators(self) -> MaterialOperators:
        """Material operators."""
        return self._implementation.material_operators

    @property
    def material_names(self) -> Dict[str, int]:
        """Get material name to DPF material ID map."""
        return self._implementation.material_names

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
        return self._implementation.get_mesh(composite_definition_label)

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
        return self._implementation.get_layup_operator(composite_definition_label)

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
        return self._implementation.evaluate_failure_criteria(
            combined_criterion, composite_scope, measure, write_data_for_full_element_scope
        )

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
        return self._implementation.get_sampling_point(
            combined_criterion, element_id, time, composite_definition_label
        )

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
        return self._implementation.get_element_info(element_id, composite_definition_label)

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
        return self._implementation.get_property_for_all_layers(
            layup_property, element_id, composite_definition_label
        )

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
        return self._implementation.get_analysis_plies(element_id, composite_definition_label)

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
        return self._implementation.get_element_laminate_offset(
            element_id, composite_definition_label
        )

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
        return self._implementation.get_constant_property_dict(
            material_properties, composite_definition_label
        )

    def get_result_times_or_frequencies(self) -> NDArray[np.double]:
        """Get the times or frequencies in the result file."""
        return self._implementation.get_result_times_or_frequencies()

    def add_interlaminar_normal_stresses(
        self,
        stresses: FieldsContainer,
        strains: FieldsContainer,
        composite_definition_label: Optional[str] = None,
    ) -> None:
        """Add interlaminar normal stresses to the stresses fields container.

        Interlaminar normal stresses (s3) are not available for layered shells.
        This function performs a post-processing step which computes s3 and adds
        it to the stress field. s3 is automatically computed if a formulation
        of a failure criterion depends on this stress component, for instance
        :class:`Puck 3D <.failure_criteria.PuckCriterion>` .

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
        self._implementation.add_interlaminar_normal_stresses(
            stresses, strains, composite_definition_label
        )

    def get_all_layered_element_ids(self) -> Sequence[int]:
        """Get all element IDs with lay-up data."""
        return self._implementation.get_all_layered_element_ids()

    def get_all_layered_element_ids_for_composite_definition_label(
        self, composite_definition_label: Optional[str] = None
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
        return self._implementation.get_all_layered_element_ids_for_composite_definition_label(
            composite_definition_label
        )
