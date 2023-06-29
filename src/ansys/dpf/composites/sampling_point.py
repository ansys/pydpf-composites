"""Wrapper for the sampling point operator."""
import json
from typing import Any, Collection, Dict, List, Sequence, Union

import numpy as np
import numpy.typing as npt

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
from ._sampling_point_types import FailureResult, SamplingPointFigure, SamplingPointProtocol
from .constants import Spot
from .failure_criteria import CombinedFailureCriterion
from .result_definition import FailureMeasureEnum


class SamplingPoint(SamplingPointProtocol):
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
        name: str,
        element_id: int,
        time_id: int,
        combined_criterion: CombinedFailureCriterion
        # rst_stream_provider: dpf.Operator,
        # material_provider: dpf.Operator,
        # material_support_provider: dpf.Operator,
        # result_info_provider: dpf.Operator,
        # layup_provider: dpf.Operator
    ):
        """Create a ``SamplingPoint`` object."""
        self.name = name
        self._element_id = element_id
        self._time_id = time_id
        self._rst_stream_provider = rst_stream_provider
        self._material_provider = material_provider
        self._material_support_provider = material_support_provider
        # todo: check if that is used
        self._result_info_provider = result_info_provider
        self._layup_provider = layup_provider

        self._spots_per_ply = 0
        self._interface_indices: Dict[Spot, int] = {}
        self._results: Any = None

    @property
    def element_id(self) -> Union[int, None]:
        """Element label for sampling the laminate."""
        return self._element_id

    @element_id.setter
    def element_id(self, value: int) -> None:
        self._element_id = value
        self._isuptodate = False

    @property
    def results(self) -> Any:
        """Results of the sampling point operator as a JSON dictionary."""
        self._update_and_check_results()
        return super().results

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
        return get_data_from_sp_results(
            "results", "failures", "failure_modes", results=self.results
        )

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
        return self._isuptodate

    def run(self) -> None:
        """Run the DPF operator and cache the results."""
        # todo: implement operator network
        result_as_string = ""

        # update internal members
        self._results = json.loads(result_as_string)
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

        self._isuptodate = True

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
        return get_indices_from_sp(self._interface_indices, self.number_of_plies, self.spots_per_ply, spots)

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
        return get_offsets_by_spots_from_sp(self, spots, core_scale_factor)

    def get_ply_wise_critical_failures(self) -> List[FailureResult]:
        """Get the critical failure value and modes per ply."""
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
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")
