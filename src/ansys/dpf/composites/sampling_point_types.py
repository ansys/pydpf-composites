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
import dataclasses
from typing import Any, Protocol

import numpy as np
import numpy.typing as npt

from .constants import Spot
from .result_definition import FailureMeasureEnum

__all__ = (
    "SamplingPointFigure",
    "FailureResult",
    "SamplingPoint",
    "FAILURE_MODE_NAMES_TO_ACP",
)


@dataclasses.dataclass(frozen=True)
class SamplingPointFigure:
    """Provides the sampling point figure and axes."""

    figure: Any
    axes: Any


@dataclasses.dataclass(frozen=True)
class FailureResult:
    """Provides the components of a failure result."""

    mode: str
    inverse_reserve_factor: float
    safety_factor: float
    safety_margin: float


FAILURE_MODE_NAMES_TO_ACP = {
    FailureMeasureEnum.INVERSE_RESERVE_FACTOR: "inverse_reserve_factor",
    FailureMeasureEnum.RESERVE_FACTOR: "reserve_factor",
    FailureMeasureEnum.MARGIN_OF_SAFETY: "margin_of_safety",
}


class SamplingPoint(Protocol):
    """Implements the ``Sampling Point`` object that wraps the DPF sampling point operator.

    Use :meth:`.CompositeModel.get_sampling_point` to get a sampling point object.
    This class provides for plotting the lay-up and results at a certain point of the
    layered structure. The results, including ``analysis_plies``, ``e1``, ``s12``, and
    ``failure_modes``, are always from the bottom to the top of the laminate (along
    the element normal direction). Postprocessing results such as ``e1`` are returned
    as flat arrays where ``self.spots_per_ply`` can be used to compute the index for
    a certain ply.

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

    @property
    def name(self) -> str:
        """Name of the object."""

    @name.setter
    def name(self, value: str) -> None:
        """Setter of name."""

    @property
    def element_id(self) -> int | None:
        """Element label for sampling the laminate.

        This attribute returns ``-1`` if the element ID is not set.
        """

    @property
    def spots_per_ply(self) -> int:
        """Number of through-the-thickness integration points per ply."""

    @property
    def results(self) -> Any:
        """Results of the sampling point results as a JSON dictionary."""

    @property
    def analysis_plies(self) -> Sequence[Any]:
        """List of analysis plies from the bottom to the top.

        This attribute returns a list of ply data, such as angle, thickness and material name,
        as a dictionary.
        """

    @property
    def s1(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 1 direction of each ply."""

    @property
    def s2(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 2 direction of each ply."""

    @property
    def s3(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 3 direction of each ply."""

    @property
    def s12(self) -> npt.NDArray[np.float64]:
        """In-plane shear stresses s12 of each ply."""

    @property
    def s13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s13 of each ply."""

    @property
    def s23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s23 of each ply."""

    @property
    def e1(self) -> npt.NDArray[np.float64]:
        """Strains in the material 1 direction of each ply."""

    @property
    def e2(self) -> npt.NDArray[np.float64]:
        """Strains in the material 2 direction of each ply."""

    @property
    def e3(self) -> npt.NDArray[np.float64]:
        """Strains in the material 3 direction of each ply."""

    @property
    def e12(self) -> npt.NDArray[np.float64]:
        """In-plane shear strains e12 of each ply."""

    @property
    def e13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e13 of each ply."""

    @property
    def e23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e23 of each ply."""

    @property
    def inverse_reserve_factor(self) -> npt.NDArray[np.float64]:
        """Critical inverse reserve factor of each ply."""

    @property
    def reserve_factor(self) -> npt.NDArray[np.float64]:
        """Lowest reserve factor of each ply.

        This attribute is equivalent to the safety factor.
        """

    @property
    def margin_of_safety(self) -> npt.NDArray[np.float64]:
        """Lowest margin of safety of each ply.

        This attribute is equivalent to the safety margin.
        """

    @property
    def failure_modes(self) -> Sequence[str]:
        """Critical failure mode of each ply."""

    @property
    def offsets(self) -> npt.NDArray[np.float64]:
        """Z coordinates for each interface and ply."""

    @property
    def polar_properties_E1(self) -> npt.NDArray[np.float64]:
        """Polar property E1 of the laminate."""

    @property
    def polar_properties_E2(self) -> npt.NDArray[np.float64]:
        """Polar property E2 of the laminate."""

    @property
    def polar_properties_G12(self) -> npt.NDArray[np.float64]:
        """Polar property G12 of the laminate."""

    @property
    def number_of_plies(self) -> int:
        """Number of plies."""

    @property
    def is_uptodate(self) -> bool:
        """True if the Sampling Point is up-to-date."""

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

    def get_ply_wise_critical_failures(self) -> list[FailureResult]:
        """Get the critical failure value and modes per ply."""

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

    def add_ply_sequence_to_plot(self, axes: Any, core_scale_factor: float = 1.0) -> None:
        """Add the stacking (ply and text) to an axis or plot.

        Parameters
        ----------
        axes :
            Matplotlib :py:class:`~matplotlib.axes.Axes` object.
        core_scale_factor :
            Factor for scaling the thickness of core plies.
        """

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
