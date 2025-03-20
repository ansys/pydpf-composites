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

"""Wrapper for the sampling point operator."""
from collections.abc import Collection, Sequence
import json
from typing import Any

from ansys.dpf.core import UnitSystem
import numpy as np
import numpy.typing as npt

from ansys.dpf import core as dpf

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
from .constants import Spot
from .failure_criteria import CombinedFailureCriterion
from .layup_info._layup_info import _get_layup_model_context
from .layup_info.material_operators import MaterialOperators
from .result_definition import FailureMeasureEnum
from .sampling_point_types import FailureResult, SamplingPoint, SamplingPointFigure
from .server_helpers import version_equal_or_later
from .unit_system import get_unit_system


class SamplingPointNew(SamplingPoint):
    """Implements the ``Sampling Point`` object that wraps the DPF sampling point operator.

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

    Notes
    -----
    The results of layered elements are stored per integration point. A layered shell element
    has a number of in-plane integration points (depending on the integration scheme) and
    typically three integration points through the thickness. The through-the-thickness
    integration points are called `spots`. They are typically at the ``BOTTOM``, ``MIDDLE``,
    and ``TOP`` of the layer. This notation is used here to identify the corresponding data.

    The ``SamplingPoint`` class returns three results per layer (one for each spot) because
    the results of the in-plane integration points are interpolated to the centroid of the element.
    The following table shows an example of a laminate with three layers. So a result, such as
    ``s1`` has nine values, three for each ply.

    +------------+------------+------------------------+
    | Layer      | Index      | Spot                   |
    +============+============+========================+
    |            | - 8        | - TOP of Layer 3       |
    | Layer 3    | - 7        | - MIDDLE of Layer 3    |
    |            | - 6        | - BOTTOM of Layer 3    |
    +------------+------------+------------------------+
    |            | - 5        | - TOP of Layer 2       |
    | Layer 2    | - 4        | - MIDDLE of Layer 2    |
    |            | - 3        | - BOTTOM of Layer 2    |
    +------------+------------+------------------------+
    |            | - 2        | - TOP of Layer 1       |
    | Layer 1    | - 1        | - MIDDLE of Layer 1    |
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
        default_unit_system: UnitSystem | None = None,
        time: float | None = None,
    ):
        """Create a ``SamplingPoint`` object."""
        self._name = name
        self._element_id = element_id
        self._time = time
        self._combined_criterion = combined_criterion

        self._material_operators = material_operators
        self._meshed_region = meshed_region
        self._layup_provider = layup_provider
        self._rst_streams_provider = rst_streams_provider

        self._spots_per_ply = 0
        self._interface_indices: dict[Spot, int] = {}
        self._results: Any = None
        self._is_uptodate = False
        self._unit_system = get_unit_system(self._rst_streams_provider, default_unit_system)

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
        self._update_and_check_results()
        return get_data_from_sp_results("layup", "polar_properties", "E1", results=self.results)

    @property
    def polar_properties_E2(self) -> npt.NDArray[np.float64]:
        """Polar property E2 of the laminate."""
        self._update_and_check_results()
        return get_data_from_sp_results("layup", "polar_properties", "E2", results=self.results)

    @property
    def polar_properties_G12(self) -> npt.NDArray[np.float64]:
        """Polar property G12 of the laminate."""
        self._update_and_check_results()
        return get_data_from_sp_results("layup", "polar_properties", "G12", results=self.results)

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
        scope_config_reader_op = dpf.Operator("composite::scope_config_reader")
        scope_config = dpf.DataTree()
        if self._time:
            scope_config.add({"requested_times": [self._time]})
        scope_config_reader_op.inputs.scope_configuration(scope_config)

        evaluate_failure_criterion_per_scope_op = dpf.Operator(
            "composite::evaluate_failure_criterion_per_scope"
        )

        # Live evaluation is not yet supported
        evaluate_failure_criterion_per_scope_op.inputs.criterion_configuration(
            self.combined_criterion.to_json()
        )

        evaluate_failure_criterion_per_scope_op.inputs.scope_configuration(
            scope_config_reader_op.outputs
        )

        scope = dpf.Scoping()
        scope.ids = [self.element_id]
        evaluate_failure_criterion_per_scope_op.inputs.element_scoping(scope)
        evaluate_failure_criterion_per_scope_op.inputs.materials_container(
            self._material_operators.material_provider.outputs
        )
        evaluate_failure_criterion_per_scope_op.inputs.stream_provider(self._rst_streams_provider)
        evaluate_failure_criterion_per_scope_op.inputs.mesh(self._meshed_region)
        # pylint: disable=protected-access
        if version_equal_or_later(self._meshed_region._server, "8.0"):
            layup_model_context = _get_layup_model_context(self._layup_provider)
            evaluate_failure_criterion_per_scope_op.inputs.layup_model_context_type(
                layup_model_context
            )
        else:
            evaluate_failure_criterion_per_scope_op.inputs.has_layup_provider(True)
        evaluate_failure_criterion_per_scope_op.inputs.section_data_container(
            self._layup_provider.outputs.section_data_container
        )

        evaluate_failure_criterion_per_scope_op.inputs.material_fields(
            self._layup_provider.outputs.material_fields
        )
        evaluate_failure_criterion_per_scope_op.inputs.mesh_properties_container(
            self._layup_provider.outputs.mesh_properties_container
        )
        evaluate_failure_criterion_per_scope_op.inputs.request_sandwich_results(True)

        sampling_point_evaluator = dpf.Operator("composite::evaluate_sampling_point")

        sampling_point_evaluator.inputs.materials_container(
            self._material_operators.material_provider.outputs
        )
        sampling_point_evaluator.inputs.material_support(
            self._material_operators.material_support_provider.outputs
        )
        sampling_point_evaluator.inputs.mesh(self._meshed_region)
        sampling_point_evaluator.inputs.stresses_container(
            evaluate_failure_criterion_per_scope_op.outputs.stresses_container
        )
        sampling_point_evaluator.inputs.strains_container(
            evaluate_failure_criterion_per_scope_op.outputs.strains_container
        )
        sampling_point_evaluator.inputs.element_scoping(scope)
        sampling_point_evaluator.inputs.section_data_container(
            self._layup_provider.outputs.section_data_container
        )

        sampling_point_evaluator.inputs.time_id(
            evaluate_failure_criterion_per_scope_op.outputs.time_id
        )
        sampling_point_evaluator.inputs.unit_system(self._unit_system)
        sampling_point_evaluator.inputs.failure_container(
            evaluate_failure_criterion_per_scope_op.outputs.failure_container
        )
        sampling_point_evaluator.inputs.extract_max_failure_per_layer(False)
        sampling_point_evaluator.inputs.check_mechanical_unit_system(False)

        sampling_point_to_json_converter = dpf.Operator("composite::convert_sampling_point_to_json")
        sampling_point_to_json_converter.connect(0, sampling_point_evaluator, 0)

        # update internal members
        self._results = json.loads(
            sampling_point_to_json_converter.get_output(pin=0, output_type=dpf.types.string)
        )
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
            self._interface_indices = {Spot.BOTTOM: 0, Spot.MIDDLE: 1, Spot.TOP: 2}
        elif self._spots_per_ply == 2:
            self._interface_indices = {Spot.BOTTOM: 0, Spot.TOP: 1}
        elif self._spots_per_ply == 1:
            raise RuntimeError(
                "Result files that only have results at the middle of the ply are not supported."
            )

        self._is_uptodate = True

    def get_indices(
        self, spots: Collection[Spot] = (Spot.BOTTOM, Spot.MIDDLE, Spot.TOP)
    ) -> Sequence[int]:
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
        spots: Collection[Spot] = (Spot.BOTTOM, Spot.MIDDLE, Spot.TOP),
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
        spots: Collection[Spot] = (Spot.BOTTOM, Spot.MIDDLE, Spot.TOP),
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
        return get_result_plots_from_sp(
            self,
            strain_components,
            stress_components,
            failure_components,
            show_failure_modes,
            create_laminate_plot,
            core_scale_factor,
            spots,
        )

    def _update_and_check_results(self) -> None:
        if not self._is_uptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")
