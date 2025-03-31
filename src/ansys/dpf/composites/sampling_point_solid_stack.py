# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""Implements sampling point functionality for a stack of solid elements."""
from collections.abc import Collection, Sequence
from typing import Any

from ansys.dpf.core import UnitSystem
from matplotlib.patches import Rectangle
import numpy as np
import numpy.typing as npt

from ansys.dpf import core as dpf
from ansys.dpf.composites.constants import (
    FailureOutput,
    Spot,
    Sym3x3TensorComponent,
    strain_component_name,
    stress_component_name,
)

from ._sampling_point_helpers import (
    add_ply_sequence_to_plot_to_sp,
    add_results_to_plot_to_sp,
    get_analysis_plies_from_sp,
    get_data_from_sp_results,
    get_indices_from_sp,
    get_offsets_by_spots_from_sp,
    get_ply_wise_critical_failures_from_sp,
    get_polar_plot_from_sp,
    get_result_plots_from_sp,
)
from .failure_criteria import CombinedFailureCriterion
from .layup_info import (
    AnalysisPlyInfoProvider,
    ElementInfoProviderProtocol,
    SolidStack,
    SolidStackProvider,
)
from .layup_info._layup_info import (
    _get_layup_model_context,
    get_material_names_to_dpf_material_index,
)
from .layup_info.material_operators import MaterialOperators
from .layup_info.material_properties import get_material_metadata
from .result_definition import FailureMeasureEnum
from .sampling_point_types import FailureResult, SamplingPoint, SamplingPointFigure
from .server_helpers import version_older_than
from .solid_stack_results import (
    get_through_the_thickness_failure_results,
    get_through_the_thickness_results,
)
from .unit_system import get_unit_system


class SamplingPointSolidStack(SamplingPoint):
    """Implements the ``Sampling Point`` object for a stack of solid elements.

    This class provides for plotting the lay-up and results at a certain point of the
    layered structure. The results, including ``analysis_plies``, ``e1``, ``s12``, and
    ``failure_modes``, are always from the bottom to the top of the laminate (along
    the element normal direction). Postprocessing results such as ``e1`` are returned
    as flat arrays where ``self.spots_per_ply`` can be used to compute the index for
    a certain ply.

    Parameters
    ----------
    name :
        Name of the object.
    element_id :
       Element label of a solid element. The sampling will automatically select to
       full stack of solid elements where this element is located.

    Notes
    -----
    The results of layered elements are stored per integration point. A layered solid element
    has a number of in-plane integration points (depending on the integration scheme) and
    two integration points through the thickness for each layer.
    The through-the-thickness integration points are called `spots`. They are typically
    at the ``BOTTOM`` and ``TOP`` of the layer. This notation is used here to identify the
    corresponding data. Note that ``MIDDLE`` is not available for solid elements.

    The ``SamplingPoint`` class for solid elements returns two results per layer (one for each spot)
    because the results of the in-plane integration points are interpolated to the centroid of
    the element. The following table shows an example of a laminate with three layers.
    So a result, such as ``s1`` has six values, two for each ply.

    +------------+------------+------------------------+
    | Layer      | Index      | Spot                   |
    +============+============+========================+
    | Layer 3    | - 5        | - TOP of Layer 3       |
    |            | - 4        | - BOTTOM of Layer 3    |
    +------------+------------+------------------------+
    | Layer 2    | - 3        | - TOP of Layer 2       |
    |            | - 2        | - BOTTOM of Layer 2    |
    +------------+------------+------------------------+
    | Layer 1    | - 1        | - TOP of Layer 1       |
    |            | - 0        | - BOTTOM of Layer 1    |
    +------------+------------+------------------------+

    The get_indices and get_offsets_by_spots methods simplify the indexing and
    filtering of the data.
    """

    def __init__(
        self,
        *,
        name: str,
        element_id: int,
        combined_criterion: CombinedFailureCriterion,
        material_operators: MaterialOperators,
        meshed_region: dpf.MeshedRegion,
        layup_provider: dpf.Operator,
        rst_streams_provider: dpf.Operator,
        element_info_provider: ElementInfoProviderProtocol,
        default_unit_system: UnitSystem | None = None,
        time: float | None = None,
    ):
        """Create a ``SamplingPoint`` object."""
        if version_older_than(meshed_region._server, "10.0"):
            raise RuntimeError(
                "DPF server version 10.0 (2025 R2) or later is required"
                " for the support of sampling points for solids."
            )

        self._name = name
        self._element_id = element_id
        self._time = time
        self._combined_criterion = combined_criterion

        self._material_operators = material_operators
        self._meshed_region = meshed_region
        self._layup_provider = layup_provider
        self._rst_streams_provider = rst_streams_provider
        self._element_info_provider = element_info_provider
        self._solid_stack_provider = SolidStackProvider(self._meshed_region, self._layup_provider)

        self._spots_per_ply = 0
        self._interface_indices: dict[Spot, int] = {}
        self._results: Any = None
        self._is_uptodate = False
        self._unit_system = get_unit_system(self._rst_streams_provider, default_unit_system)
        self._solid_stack: SolidStack | None = None

    @property
    def name(self) -> str:
        """Name of the object."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set object name."""
        self._name = value

    @property
    def element_id(self) -> int | None:
        """Element label for sampling the laminate."""
        return self._element_id

    @element_id.setter
    def element_id(self, value: int) -> None:
        self._element_id = value
        self._is_uptodate = False

    @property
    def combined_criterion(self) -> CombinedFailureCriterion:
        """Element label for sampling the laminate."""
        return self._combined_criterion

    @combined_criterion.setter
    def combined_criterion(self, value: CombinedFailureCriterion) -> None:
        self._combined_criterion = value
        self._is_uptodate = False

    @property
    def spots_per_ply(self) -> int:
        """Number of through-the-thickness integration points per ply."""
        return self._spots_per_ply

    @property
    def results(self) -> Any:
        """Results of the sampling point operator as a JSON dictionary."""
        self._update_and_check_results()
        return self._results

    @property
    def analysis_plies(self) -> Sequence[Any]:
        """List of analysis plies from the bottom to the top.

        This attribute returns a list of ply data, such as angle, thickness and material name,
        as a dictionary.
        """
        self._update_and_check_results()
        return get_analysis_plies_from_sp(self.results)

    @property
    def s1(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 1 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s1", results=self.results)

    @property
    def s2(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 2 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s2", results=self.results)

    @property
    def s3(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 3 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s3", results=self.results)

    @property
    def s12(self) -> npt.NDArray[np.float64]:
        """In-plane shear stresses s12 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s12", results=self.results)

    @property
    def s13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s13 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s13", results=self.results)

    @property
    def s23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s23 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "stresses", "s13", results=self.results)

    @property
    def e1(self) -> npt.NDArray[np.float64]:
        """Strains in the material 1 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e1", results=self.results)

    @property
    def e2(self) -> npt.NDArray[np.float64]:
        """Strains in the material 2 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e2", results=self.results)

    @property
    def e3(self) -> npt.NDArray[np.float64]:
        """Strains in the material 3 direction of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e3", results=self.results)

    @property
    def e12(self) -> npt.NDArray[np.float64]:
        """In-plane shear strains e12 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e12", results=self.results)

    @property
    def e13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e13 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e13", results=self.results)

    @property
    def e23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e23 of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "strains", "e23", results=self.results)

    @property
    def inverse_reserve_factor(self) -> npt.NDArray[np.float64]:
        """Critical inverse reserve factor of each ply."""
        self._update_and_check_results()
        return get_data_from_sp_results(
            "results", "failures", "inverse_reserve_factor", results=self.results
        )

    @property
    def reserve_factor(self) -> npt.NDArray[np.float64]:
        """Lowest reserve factor of each ply.

        This attribute is equivalent to the safety factor.
        """
        self._update_and_check_results()
        return get_data_from_sp_results(
            "results", "failures", "reserve_factor", results=self.results
        )

    @property
    def margin_of_safety(self) -> npt.NDArray[np.float64]:
        """Lowest margin of safety of each ply.

        This attribute is equivalent to the safety margin.
        """
        self._update_and_check_results()
        return get_data_from_sp_results(
            "results", "failures", "margin_of_safety", results=self.results
        )

    @property
    def failure_modes(self) -> Sequence[str]:
        """Critical failure mode of each ply."""
        self._update_and_check_results()
        return list(self.results[0]["results"]["failures"]["failure_modes"])

    @property
    def offsets(self) -> npt.NDArray[np.float64]:
        """Z coordinates for each interface and ply."""
        self._update_and_check_results()
        return get_data_from_sp_results("results", "offsets", results=self.results)

    @property
    def polar_properties_E1(self) -> npt.NDArray[np.float64]:
        """Polar property E1 of the laminate."""
        raise NotImplementedError(
            "Polar properties are not implemented for the sampling point for a solid elements."
        )

    @property
    def polar_properties_E2(self) -> npt.NDArray[np.float64]:
        """Polar property E2 of the laminate."""
        raise NotImplementedError(
            "Polar properties are not implemented for the sampling point for a solid elements."
        )

    @property
    def polar_properties_G12(self) -> npt.NDArray[np.float64]:
        """Polar property G12 of the laminate."""
        raise NotImplementedError(
            "Polar properties are not implemented for the sampling point for a solid elements."
        )

    @property
    def number_of_plies(self) -> int:
        """Number of plies."""
        return len(self.analysis_plies)

    @property
    def is_uptodate(self) -> bool:
        """True if the results are up-to-date."""
        return self._is_uptodate

    def run(self) -> None:
        """Build and run the DPF operator network and cache the results."""
        if not self.element_id:
            raise RuntimeError("Element ID must be set before running the sampling point.")

        # Get solid stack to select all the elements in the stack
        self._solid_stack = self._solid_stack_provider.get_solid_stack(self.element_id)
        if not self._solid_stack:
            raise RuntimeError(f"Solid stack for element {self.element_id} not found.")

        element_scope = dpf.Scoping(location="elemental")
        element_scope.ids = self._solid_stack.element_ids

        stress_operator = dpf.operators.result.stress()
        stress_operator.inputs.streams_container.connect(self._rst_streams_provider)
        stress_operator.inputs.bool_rotate_to_global(False)

        elastic_strain_operator = dpf.operators.result.elastic_strain()
        elastic_strain_operator.inputs.streams_container.connect(self._rst_streams_provider)
        elastic_strain_operator.inputs.bool_rotate_to_global(False)

        stress_container = stress_operator.outputs.fields_container()
        elastic_strain_container = elastic_strain_operator.outputs.fields_container()
        if not self._time:
            last_time_step = stress_container.get_available_ids_for_label("time")[-1]
            if (
                not elastic_strain_container.get_available_ids_for_label("time")[-1]
                == last_time_step
            ):
                raise RuntimeError("Time cannot be extracted. Please provide a time value.")
            self._time = last_time_step

        failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
        failure_evaluator.inputs.configuration(self.combined_criterion.to_json())
        failure_evaluator.inputs.materials_container(self._material_operators.material_provider)
        failure_evaluator.inputs.stresses_container(stress_container)
        failure_evaluator.inputs.strains_container(elastic_strain_container)
        failure_evaluator.inputs.section_data_container(
            self._layup_provider.outputs.section_data_container
        )
        failure_evaluator.inputs.mesh_properties_container(
            self._layup_provider.outputs.mesh_properties_container
        )
        failure_evaluator.inputs.layup_model_context_type(
            _get_layup_model_context(self._layup_provider)
        )
        failure_evaluator.inputs.mesh(self._meshed_region)

        elemental_nodal_failure_container = failure_evaluator.outputs.fields_container.get_data()
        irf_field = elemental_nodal_failure_container.get_field(
            {
                "failure_label": FailureOutput.FAILURE_VALUE,
                "time": self._time,
            }
        )
        failure_model_field = elemental_nodal_failure_container.get_field(
            {
                "failure_label": FailureOutput.FAILURE_MODE,
                "time": self._time,
            }
        )

        failure_results = get_through_the_thickness_failure_results(
            self._solid_stack, self._element_info_provider, irf_field, failure_model_field
        )

        stress_field = stress_container.get_field(
            {
                "time": self._time,
            }
        )
        elastic_strain_field = elastic_strain_container.get_field(
            {
                "time": self._time,
            }
        )

        stress_results = get_through_the_thickness_results(
            self._solid_stack,
            self._element_info_provider,
            stress_field,
            tuple(stress_component_name(component) for component in Sym3x3TensorComponent),
        )
        strain_results = get_through_the_thickness_results(
            self._solid_stack,
            self._element_info_provider,
            elastic_strain_field,
            tuple([strain_component_name(component) for component in Sym3x3TensorComponent]),
        )

        analysis_plies = []
        offsets = []

        material_ids_to_dpf_index = get_material_names_to_dpf_material_index(
            self._material_operators.material_container_helper_op
        )
        material_meta_data = get_material_metadata(
            self._material_operators.material_container_helper_op
        )
        for index, ply_id_and_th in enumerate(self._solid_stack.analysis_ply_ids_and_thicknesses):
            ap_info_provider = AnalysisPlyInfoProvider(self._meshed_region, ply_id_and_th[0])
            ap_inf = ap_info_provider.basic_info()

            dpf_mat_index = material_ids_to_dpf_index[ap_inf.material_name]
            analysis_plies.append(
                {
                    "angle": ap_inf.angle,
                    "global_ply_number": ap_inf.global_ply_number,
                    "id": ply_id_and_th[0],
                    "is_core": material_meta_data[dpf_mat_index].is_core,
                    "material": ap_inf.material_name,
                    "thickness": ply_id_and_th[1],
                }
            )

            if index == 0:
                offsets.extend([0.0, ply_id_and_th[1]])
            else:
                offsets.append(offsets[-1])
                offsets.append(offsets[-1] + ply_id_and_th[1])

        self._results = [
            {
                "element_label": self._element_id,
                "layup": {
                    "analysis_plies": analysis_plies,
                    "num_analysis_plies": self._solid_stack.number_of_analysis_plies,
                    "offset": 0.0,
                    "polar_properties": None,
                },
                "results": {
                    "failures": {
                        "failure_modes": [failure_res.mode for failure_res in failure_results],
                        "inverse_reserve_factor": [
                            failure_res.inverse_reserve_factor for failure_res in failure_results
                        ],
                        "margin_of_safety": [
                            failure_res.safety_margin for failure_res in failure_results
                        ],
                        "reserve_factor": [
                            failure_res.safety_factor for failure_res in failure_results
                        ],
                    },
                    "strains": {
                        "e1": strain_results["e1"],
                        "e12": strain_results["e12"],
                        "e13": strain_results["e13"],
                        "e2": strain_results["e2"],
                        "e23": strain_results["e23"],
                        "e3": strain_results["e3"],
                    },
                    "stresses": {
                        "s1": stress_results["s1"],
                        "s12": stress_results["s12"],
                        "s13": stress_results["s13"],
                        "s2": stress_results["s2"],
                        "s23": stress_results["s23"],
                        "s3": stress_results["s3"],
                    },
                    "offsets": offsets,
                },
                "unit_system": self._unit_system.name,
            }
        ]

        if not self._results or len(self._results) == 0:
            raise RuntimeError(f"Sampling point {self.name} has no results.")
        if self._results and len(self._results) > 1:
            raise RuntimeError(
                f"Sampling point {self.name} is scoped to more than one element,"
                f" which is not yet supported."
            )

        self._spots_per_ply = 0
        if self._results:
            # update the number of spots
            self._spots_per_ply = int(
                len(np.array(self._results[0]["results"]["strains"]["e1"]))
                / len(self._results[0]["layup"]["analysis_plies"])
            )

        if self._spots_per_ply == 3:
            raise RuntimeError("Sampling Point for a solid stack can have only 2 spots per ply.")
        elif self._spots_per_ply == 2:
            self._interface_indices = {Spot.BOTTOM: 0, Spot.TOP: 1}
        elif self._spots_per_ply == 1:
            raise RuntimeError(
                "Result files that only have results at the middle of the ply are not supported."
            )
        else:
            raise RuntimeError(f"Invalid number of spots ({self._spots_per_ply}) per ply.")

        self._is_uptodate = True

    def get_indices(self, spots: Collection[Spot] = (Spot.BOTTOM, Spot.TOP)) -> Sequence[int]:
        """Get the indices of the selected spots (interfaces) for each ply.

        The indices are sorted from bottom to top.
        For instance, this method can be used to access the stresses at the bottom of each ply.

        Parameters
        ----------
        spots :
            Collection of spots. Only the indices of the bottom interfaces of plies
            are returned if ``[Spot.BOTTOM]`` is set.

        Examples
        --------
            >>> ply_top_indices = sampling_point.get_indices([Spot.TOP])

        """
        self._update_and_check_results()
        return get_indices_from_sp(
            self._interface_indices, self.number_of_plies, self.spots_per_ply, spots
        )

    def get_offsets_by_spots(
        self,
        spots: Collection[Spot] = (Spot.BOTTOM, Spot.TOP),
        core_scale_factor: float = 1.0,
    ) -> npt.NDArray[np.float64]:
        """Access the y coordinates of the selected spots (interfaces) for each ply.

        Parameters
        ----------
        spots :
            Collection of spots.

        core_scale_factor :
            Factor for scaling the thickness of core plies.
        """
        self._update_and_check_results()
        return get_offsets_by_spots_from_sp(self, spots, core_scale_factor)

    def get_ply_wise_critical_failures(self) -> list[FailureResult]:
        """Get the critical failure value and modes per ply."""
        self._update_and_check_results()
        return get_ply_wise_critical_failures_from_sp(self)

    def add_results_to_plot(
        self,
        axes: Any,
        components: Sequence[str],
        spots: Collection[Spot] = (Spot.BOTTOM, Spot.TOP),
        core_scale_factor: float = 1.0,
        title: str = "",
        xlabel: str = "",
    ) -> None:
        """Add results (strain, stress, or failure values) to an ``Axes`` object.

        Parameters
        ----------
        axes :
            Matplotlib :py:class:`~matplotlib.axes.Axes` object.
        components :
            List of result components. Valid components for
            strain are ``"e1"``, ``"e2"``, ``"e3"``, ``"e12"``, ``"e13"``,
            and ``"e23"`` Valid components for stress are ``"s1",`` ``"s2"``,
            ``"s3"``, ``"s12"``, ``"s13"``, and ``"s23"``. Valid components
            for failure are ``"inverse_reserve_factor"``, ``"reserve_factor"``,
            and ``"margin_of_safety"``.
        spots :
            Collection of spots (interfaces).
        core_scale_factor :
            Factor for scaling the thickness of core plies.
        title :
            Title of the plot. This parameter is ignored if empty.
        xlabel :
            Becomes the label of the x-axis. This parameter is ignored if empty.

        Examples
        --------
            >>> import matplotlib.pyplot as plt
            >>> fig, ax1 = plt.subplots()
            >>> sampling_point.add_results_to_plot(ax1,
                                                  ["s13", "s23", "s3"],
                                                  [Spot.BOTTOM, Spot.TOP],
                                                  0.1, "Interlaminar Stresses", "[MPa]")
        """
        self._update_and_check_results()
        add_results_to_plot_to_sp(self, axes, components, spots, core_scale_factor, title, xlabel)

    def add_ply_sequence_to_plot(self, axes: Any, core_scale_factor: float = 1.0) -> None:
        """Add the stacking (ply and text) to an axis or plot.

        Parameters
        ----------
        axes :
            Matplotlib :py:class:`~matplotlib.axes.Axes` object.
        core_scale_factor :
            Factor for scaling the thickness of core plies.
        """
        self._update_and_check_results()
        add_ply_sequence_to_plot_to_sp(self, axes, core_scale_factor)

    def get_polar_plot(
        self, components: Sequence[str] = ("E1", "E2", "G12")
    ) -> SamplingPointFigure:
        """Create a standard polar plot to visualize the polar properties of the laminate.

        Parameters
        ----------
        components :
            Stiffness quantities to plot.

        Examples
        --------
            >>> figure, axes = sampling_point.get_polar_plot(components=["E1", "G12"])
        """
        self._update_and_check_results()
        return get_polar_plot_from_sp(self, components)

    def get_result_plots(
        self,
        strain_components: Sequence[str] = ("e1", "e2", "e3", "e12", "e13", "e23"),
        stress_components: Sequence[str] = ("s1", "s2", "s3", "s12", "s13", "s23"),
        failure_components: Sequence[FailureMeasureEnum] = (
            FailureMeasureEnum.INVERSE_RESERVE_FACTOR,
            FailureMeasureEnum.RESERVE_FACTOR,
            FailureMeasureEnum.MARGIN_OF_SAFETY,
        ),
        show_failure_modes: bool = False,
        create_laminate_plot: bool = True,
        core_scale_factor: float = 1.0,
        spots: Collection[Spot] = (Spot.BOTTOM, Spot.TOP),
    ) -> SamplingPointFigure:
        """Generate a figure with a grid of axes (plot) for each selected result entity.

        Parameters
        ----------
        strain_components
            Strain entities of interest. Supported values are ``"e1"``, ``"e2"``,
            ``"e3"``, ``"e12"``, ``"e13"``, and ``"e23"``. The plot is skipped
            if the list is empty.
        stress_components
            Stress entities of interest. Supported values are ``"s1"``, ``"s2"``,
            ``"s3"``, ``"s12"``, ``"s13"``, and ``"s23"``. The plot is skipped
            if the list is empty.
        failure_components
            Failure values of interest. Values supported are ``"irf"``, ``"rf"``,
            and ``"mos"``. The plot is skipped if the list is empty.
        show_failure_modes
            WHether to add the critical failure mode to the failure plot.
        create_laminate_plot
            Whether to plot the stacking sequence of the laminate, including text information
            such as material, thickness, and angle.
        core_scale_factor
            Factor for scaling the thickness of core plies.
        spots
            Spots (interfaces) to show results at.

        Examples
        --------
            >>> figure, axes = sampling_point.get_result_plots()

        """
        self._update_and_check_results()
        sp_figure = get_result_plots_from_sp(
            self,
            strain_components,
            stress_components,
            failure_components,
            show_failure_modes,
            create_laminate_plot,
            core_scale_factor,
            spots,
        )
        if create_laminate_plot:
            self.add_element_boxes_to_plot(sp_figure.axes[0], core_scale_factor)

        return sp_figure

    def add_element_boxes_to_plot(
        self, axes: Any, core_scale_factor: float = 1.0, alpha: float = 0.2
    ) -> None:
        """Add the element stack (boxes) to an axis or plot.

        Parameters
        ----------
        axes :
            Matplotlib :py:class:`~matplotlib.axes.Axes` object.
        core_scale_factor :
            Factor for scaling the thickness of core plies.
        alpha :
            Transparency of the element boxes.
        """
        if not self._solid_stack:
            raise RuntimeError("Solid stack is not available.")

        self._update_and_check_results()
        plY_offsets = self.get_offsets_by_spots(
            spots=[Spot.BOTTOM, Spot.TOP], core_scale_factor=core_scale_factor
        )

        element_offsets = []
        ply_index = 0
        for _, element_ids in self._solid_stack.element_ids_per_level.items():
            element_ply_ids = self._solid_stack.element_wise_analysis_plies[element_ids[0]]
            element_offsets.append(plY_offsets[2 * ply_index])
            ply_index += len(element_ply_ids)
            element_offsets.append(plY_offsets[2 * ply_index - 1])

        if len(element_offsets) == 0:
            return

        num_spots = 2
        axes.set_ybound(element_offsets[0], element_offsets[-1])
        x_bound = axes.get_xbound()
        width = x_bound[1] - x_bound[0]

        colors = ("b", "g", "r", "c", "m", "y")
        for index, _ in enumerate(self._solid_stack.element_ids_per_level):
            hatch = ""
            axes.add_patch(
                Rectangle(
                    xy=(float(x_bound[0]), float(element_offsets[index * num_spots])),
                    width=width,
                    height=float(
                        element_offsets[(index + 1) * num_spots - 1]
                        - element_offsets[index * num_spots]
                    ),
                    fill=True,
                    hatch=hatch,
                    alpha=alpha,
                    color=colors[index % len(colors)],
                )
            )

    def _update_and_check_results(self) -> None:
        if not self._is_uptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")
