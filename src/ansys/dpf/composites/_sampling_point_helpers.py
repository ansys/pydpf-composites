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
from typing import Any, cast

from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from .constants import Spot
from .result_definition import FailureMeasureEnum
from .sampling_point_types import (
    FAILURE_MODE_NAMES_TO_ACP,
    FailureResult,
    SamplingPoint,
    SamplingPointFigure,
)


def get_analysis_plies_from_sp(results: Any) -> Sequence[Any]:
    """List of analysis plies from the bottom to the top.

    This attribute returns a list of ply data, such as angle, thickness and material name,
    as a dictionary.
    """
    if len(results) == 0:
        raise RuntimeError("Cannot extract Analysis Plies from the Sampling Point result.")

    raw_data = cast(Sequence[Any], results[0]["layup"]["analysis_plies"])
    if len(raw_data) == 0:
        raise RuntimeError("No plies are found for the selected element.")

    types = {
        "angle": float,
        "global_ply_number": int,
        "id": str,
        "is_core": bool,
        "material": str,
        "thickness": float,
    }

    plies = []
    for raw_ply in raw_data:
        plies.append({k: types[k](v) for k, v in raw_ply.items()})

    return plies


def get_data_from_sp_results(*args: Any, results: Any) -> npt.NDArray[np.float64]:
    """Extract data from the result dict.

    The result object of the sampling point is a (nested) JSON dict. The args are the keys
    to dive into the results and extract the according data.
    For example: get_data_from_sp_results("results", "stresses", "s1", results=sp.results)
    returns the stresses in the material direction.
    """

    def _next(outer_data: Any, comp: str) -> Any:
        if comp in outer_data.keys():
            return outer_data[comp]

        raise RuntimeError(f"Cannot extract result {comp} from Sampling Point results.")

    if not results or len(results) == 0:
        raise RuntimeError(f"Cannot extract result {args} from Sampling Point result.")

    data = results[0]
    for key in args:
        data = _next(data, key)
    return np.array(data)


def get_indices_from_sp(
    interface_indices: dict[Spot, int],
    number_of_plies: int,
    spots_per_ply: int,
    spots: Collection[Spot] = (Spot.BOTTOM, Spot.MIDDLE, Spot.TOP),
) -> Sequence[int]:
    """Get the indices of the selected spots (interfaces) for each ply."""
    ply_wise_indices = [interface_indices[v] for v in spots]
    ply_wise_indices.sort()
    indices = []
    for ply_index in range(0, number_of_plies):
        indices.extend([ply_index * spots_per_ply + index for index in ply_wise_indices])

    return indices


def get_offsets_by_spots_from_sp(
    sampling_point: SamplingPoint,
    spots: Collection[Spot] = (Spot.BOTTOM, Spot.MIDDLE, Spot.TOP),
    core_scale_factor: float = 1.0,
) -> npt.NDArray[np.float64]:
    """Access the y coordinates of the selected spots (interfaces) for each ply."""
    offsets = sampling_point.offsets
    indices = sampling_point.get_indices(spots)

    if core_scale_factor == 1.0:
        return cast(npt.NDArray[np.float64], offsets[indices])

    spots_per_ply = sampling_point.spots_per_ply

    thicknesses = []
    if not sampling_point.analysis_plies:
        raise RuntimeError("No analysis plies are found in the selected element.")

    for index, ply in enumerate(sampling_point.analysis_plies):
        is_core = ply["is_core"]
        # get thickness from the offsets
        th = offsets[(index + 1) * spots_per_ply - 1] - offsets[index * spots_per_ply]
        if is_core:
            th *= core_scale_factor

        thicknesses.append(th)

    for index, ply in enumerate(sampling_point.analysis_plies):
        # spots per ply is always 2 or 3
        step = thicknesses[index] / (spots_per_ply - 1)
        top_of_previous_ply = offsets[index * spots_per_ply - 1] if index > 0 else offsets[0]
        for i in range(0, spots_per_ply):
            offsets[index * spots_per_ply + i] = top_of_previous_ply + step * i

    return cast(npt.NDArray[np.float64], offsets[indices])


def get_ply_wise_critical_failures_from_sp(
    sampling_point: SamplingPoint,
) -> list[FailureResult]:
    """Get the critical failure value and modes per ply."""
    num_plies = sampling_point.number_of_plies

    irfs = sampling_point.inverse_reserve_factor.reshape(num_plies, sampling_point.spots_per_ply)
    mos = sampling_point.margin_of_safety.reshape(num_plies, sampling_point.spots_per_ply)
    rfs = sampling_point.reserve_factor.reshape(num_plies, sampling_point.spots_per_ply)
    failure_models = np.array(sampling_point.failure_modes).reshape(
        num_plies, sampling_point.spots_per_ply
    )

    critical_indices = irfs.argmax(1)

    result = []

    for ply_index, crit_index in enumerate(critical_indices):
        result.append(
            FailureResult(
                failure_models[ply_index][crit_index],
                irfs[ply_index][crit_index],
                rfs[ply_index][crit_index],
                mos[ply_index][crit_index],
            )
        )

    return result


def get_polar_plot_from_sp(
    sampling_point: SamplingPoint, components: Sequence[str] = ("E1", "E2", "G12")
) -> SamplingPointFigure:
    """Create a standard polar plot to visualize the polar properties of the laminate."""
    if not sampling_point.is_uptodate or not sampling_point.results:
        raise RuntimeError(f"Sampling point {sampling_point.name} is out-of-date.")

    theta = (
        get_data_from_sp_results(
            "layup", "polar_properties", "angles", results=sampling_point.results
        )
        / 180.0
        * np.pi
    )
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"})

    for comp in components:
        ax.plot(theta, getattr(sampling_point, f"polar_properties_{comp}", []), label=comp)

    ax.set_title("Polar Properties")
    ax.legend()
    return SamplingPointFigure(fig, ax)


def add_ply_sequence_to_plot_to_sp(
    sampling_point: SamplingPoint, axes: Any, core_scale_factor: float = 1.0
) -> None:
    """Add the stacking (ply and text) to an axis or plot."""
    offsets = sampling_point.get_offsets_by_spots(
        spots=[Spot.BOTTOM, Spot.TOP], core_scale_factor=core_scale_factor
    )

    if len(offsets) == 0:
        return

    num_spots = 2
    axes.set_ybound(offsets[0], offsets[-1])
    x_bound = axes.get_xbound()
    width = x_bound[1] - x_bound[0]

    for index, ply in enumerate(sampling_point.analysis_plies):
        hatch = "x" if ply["is_core"] else ""

        height = offsets[(index + 1) * num_spots - 1] - offsets[index * num_spots]
        origin = (x_bound[0], offsets[index * num_spots])
        axes.add_patch(
            Rectangle(
                xy=origin,
                width=width,
                height=height,
                fill=False,
                hatch=hatch,
            )
        )
        mat = ply["material"]
        th = float(ply["thickness"])
        if "angle" in ply.keys():
            angle = float(ply["angle"])
            text = f"{mat}\nangle={angle:.3}, th={th:.3}"
        else:
            text = f"{mat}\nth={th:.3}"
        axes.annotate(
            text=text,
            xy=(origin[0] + width / 2.0, origin[1] + height / 2.0),
            ha="center",
            va="center",
            fontsize=8,
        )


def add_results_to_plot_to_sp(
    sampling_point: SamplingPoint,
    axes: Any,
    components: Sequence[str],
    spots: Collection[Spot] = (Spot.BOTTOM, Spot.TOP),
    core_scale_factor: float = 1.0,
    title: str = "",
    xlabel: str = "",
) -> None:
    """Add results (strain, stress, or failure values) to an ``Axes`` object."""
    indices = sampling_point.get_indices(spots)
    offsets = sampling_point.get_offsets_by_spots(spots, core_scale_factor)

    for comp in components:
        raw_values = getattr(sampling_point, comp)
        if raw_values is None:
            raise RuntimeError(
                f"Component {comp} is not supported. "
                f"See the description for the 'add_results_to_plot' method."
            )
        values = [raw_values[i] for i in indices]
        axes.plot(values, offsets, label=comp)
    if title:
        axes.set_title(title)
    if xlabel:
        axes.set_xlabel(xlabel)

    axes.legend()
    axes.grid()


def get_result_plots_from_sp(
    sampling_point: SamplingPoint,
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
    """Generate a figure with a grid of axes (plot) for each selected result entity."""
    num_active_plots = int(create_laminate_plot)
    num_active_plots += 1 if len(strain_components) > 0 else 0
    num_active_plots += 1 if len(stress_components) > 0 else 0
    num_active_plots += 1 if len(failure_components) > 0 else 0

    fig = plt.figure()
    gs = fig.add_gridspec(1, num_active_plots, hspace=0, wspace=0)
    axes = gs.subplots(sharex="col", sharey="row")

    def _get_subplot(axes_obj: Any, current_index: int) -> Any:
        try:
            return axes_obj[current_index]
        except TypeError as exc:
            if current_index > 0:
                raise RuntimeError(f"{type(axes_obj).__name__} plot cannot be indexed.") from exc
            return axes_obj
        except IndexError as exc:
            raise RuntimeError("get_subplot: index exceeds limit.") from exc

    if num_active_plots > 0:
        ticks = sampling_point.get_offsets_by_spots(
            spots=[Spot.TOP], core_scale_factor=core_scale_factor
        )

        axes_index = 0

        first_axis = _get_subplot(axes, axes_index)
        if core_scale_factor != 1.0:
            labels = []
            first_axis.set_ylabel("z-Coordinates (scaled)")
        else:
            labels = [f"{t:.3}" for t in ticks]
            first_axis.set_ylabel("z-Coordinates [length]")

        first_axis.set_yticks(ticks=ticks, labels=labels)

        if create_laminate_plot:
            plt.rcParams["hatch.linewidth"] = 0.2
            plt.rcParams["hatch.color"] = "silver"
            layup_axis = _get_subplot(axes, axes_index)
            sampling_point.add_ply_sequence_to_plot(layup_axis, core_scale_factor)
            layup_axis.set_xticks([])
            axes_index += 1

        if len(strain_components) > 0:
            strain_axis = _get_subplot(axes, axes_index)
            sampling_point.add_results_to_plot(
                strain_axis, strain_components, spots, core_scale_factor, "Strains", "[-]"
            )
            axes_index += 1

        if len(stress_components) > 0:
            stress_axis = _get_subplot(axes, axes_index)
            sampling_point.add_results_to_plot(
                stress_axis,
                stress_components,
                spots,
                core_scale_factor,
                "Stresses",
                "[force/area]",
            )
            axes_index += 1

        if len(failure_components) > 0:
            failure_axis = _get_subplot(axes, axes_index)
            internal_fc = [FAILURE_MODE_NAMES_TO_ACP[v] for v in failure_components]
            sampling_point.add_results_to_plot(
                failure_axis, internal_fc, spots, core_scale_factor, "Failures", "[-]"
            )

            if show_failure_modes:
                if Spot.MIDDLE in spots:
                    fm_offsets = sampling_point.get_offsets_by_spots(
                        spots=[Spot.MIDDLE], core_scale_factor=core_scale_factor
                    )
                else:
                    bot_offsets = sampling_point.get_offsets_by_spots(
                        spots=[Spot.BOTTOM], core_scale_factor=core_scale_factor
                    )
                    top_offsets = sampling_point.get_offsets_by_spots(
                        spots=[Spot.TOP], core_scale_factor=core_scale_factor
                    )
                    fm_offsets = np.array(bot_offsets + top_offsets) / np.float64(2.0)

                critical_failures = sampling_point.get_ply_wise_critical_failures()

                if len(critical_failures) != len(fm_offsets):
                    raise IndexError("Sizes of failures and offsets do not match.")

                for index, offset in enumerate(fm_offsets):
                    for fc in failure_components:
                        failure_axis.annotate(
                            getattr(critical_failures[index], "mode"),
                            xy=(getattr(critical_failures[index], fc.value), offset),
                            xytext=(getattr(critical_failures[index], fc.value), offset),
                        )

            axes_index += 1

    return SamplingPointFigure(fig, axes)
