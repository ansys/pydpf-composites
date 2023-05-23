"""Wrapper for the sampling point operator."""
import dataclasses
import hashlib
import json
from typing import Any, Collection, Dict, List, Sequence, Union, cast

import ansys.dpf.core as dpf
from ansys.dpf.core.server import get_or_create_server
from ansys.dpf.core.server_types import BaseServer
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from .constants import Spot
from .result_definition import FailureMeasure, ResultDefinition
from .server_helpers._load_plugin import load_composites_plugin

__all__ = (
    "SamplingPointFigure",
    "FailureResult",
    "SamplingPoint",
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


def _check_result_definition_has_single_scope(result_definition: ResultDefinition) -> None:
    if len(result_definition.scopes) != 1:
        raise RuntimeError(
            "Error when creating a sampling point: "
            "Result definition must have exactly one"
            "scope."
        )


class SamplingPoint:
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
    result_definition :
        Result definition object that defines all inputs and the scope.

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

    _FAILURE_MODE_NAMES_TO_ACP = {
        FailureMeasure.INVERSE_RESERVE_FACTOR: "inverse_reserve_factor",
        FailureMeasure.RESERVE_FACTOR: "reserve_factor",
        FailureMeasure.MARGIN_OF_SAFETY: "margin_of_safety",
    }

    def __init__(
        self,
        name: str,
        result_definition: ResultDefinition,
        server: BaseServer = None,
    ):
        """Create a ``SamplingPoint`` object."""
        self._spots_per_ply = 0
        self._interface_indices: Dict[Spot, int] = {}
        self.name = name
        self._result_definition = result_definition

        _check_result_definition_has_single_scope(result_definition)
        # specifies the server. Creates a new one if needed
        used_server = get_or_create_server(server)
        if not used_server:
            raise RuntimeError("SamplingPoint: cannot connect to DPF server or launch it.")

        if used_server != server:
            load_composites_plugin(used_server)

        # initialize the sampling point operator. Do it just once
        self._operator = dpf.Operator(
            name="composite::composite_sampling_point_operator", server=used_server
        )
        if not self._operator:
            raise RuntimeError("SamplingPoint: failed to initialize the operator.")

        self._results: Any = None
        self._isuptodate = False
        self._rd_hash = ""

    @property
    def result_definition(self) -> ResultDefinition:
        """Input for the sampling point operator."""
        return self._result_definition

    @result_definition.setter
    def result_definition(self, value: ResultDefinition) -> None:
        _check_result_definition_has_single_scope(value)
        self._isuptodate = False

        self._result_definition = value

    @property
    def element_id(self) -> Union[int, None]:
        """Element label for sampling the laminate.

        This attribute returns ``-1`` if the element ID is not set.
        """
        element_scope = self._result_definition.scopes[0].element_scope
        if len(element_scope) > 1:
            raise RuntimeError("The scope of a sampling point can only be one element.")
        if len(element_scope) == 0:
            return None
        return element_scope[0]

    @element_id.setter
    def element_id(self, value: int) -> None:
        self._result_definition.scopes[0].element_scope = [value]
        self._isuptodate = False

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

        raw_data = cast(Sequence[Any], self._results[0]["layup"]["analysis_plies"])
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

    @property
    def s1(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 1 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s1"])

    @property
    def s2(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 2 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s2"])

    @property
    def s3(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 3 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s3"])

    @property
    def s12(self) -> npt.NDArray[np.float64]:
        """In-plane shear stresses s12 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s12"])

    @property
    def s13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s13 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s13"])

    @property
    def s23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s23 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s23"])

    @property
    def e1(self) -> npt.NDArray[np.float64]:
        """Strains in the material 1 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e1"])

    @property
    def e2(self) -> npt.NDArray[np.float64]:
        """Strains in the material 2 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e2"])

    @property
    def e3(self) -> npt.NDArray[np.float64]:
        """Strains in the material 3 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e3"])

    @property
    def e12(self) -> npt.NDArray[np.float64]:
        """In-plane shear strains e12 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e12"])

    @property
    def e13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e13 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e13"])

    @property
    def e23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e23 of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["strains"]["e13"])

    @property
    def inverse_reserve_factor(self) -> npt.NDArray[np.float64]:
        """Critical inverse reserve factor of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["failures"]["inverse_reserve_factor"])

    @property
    def reserve_factor(self) -> npt.NDArray[np.float64]:
        """Lowest reserve factor of each ply.

        This attribute is equivalent to the safety factor.
        """
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["failures"]["reserve_factor"])

    @property
    def margin_of_safety(self) -> npt.NDArray[np.float64]:
        """Lowest margin of safety of each ply.

        This attribute is equivalent to the safety margin.
        """
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["failures"]["margin_of_safety"])

    @property
    def failure_modes(self) -> Sequence[str]:
        """Critical failure mode of each ply."""
        self._update_and_check_results()
        return cast(Sequence[str], self._results[0]["results"]["failures"]["failure_modes"])

    @property
    def offsets(self) -> npt.NDArray[np.float64]:
        """Z coordinates for each interface and ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["offsets"])

    @property
    def polar_properties_E1(self) -> npt.NDArray[np.float64]:
        """Polar property E1 of the laminate."""
        self._update_and_check_results()
        return np.array(self._results[0]["layup"]["polar_properties"]["E1"])

    @property
    def polar_properties_E2(self) -> npt.NDArray[np.float64]:
        """Polar property E2 of the laminate."""
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")

        return np.array(self._results[0]["layup"]["polar_properties"]["E2"])

    @property
    def polar_properties_G12(self) -> npt.NDArray[np.float64]:
        """Polar property G12 of the laminate."""
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")

        return np.array(self._results[0]["layup"]["polar_properties"]["G12"])

    @property
    def number_of_plies(self) -> int:
        """Number of plies."""
        return len(self.analysis_plies)

    def run(self) -> None:
        """Run the DPF operator and cache the results."""
        if self.result_definition:
            new_hash = hashlib.sha1(
                json.dumps(self.result_definition.to_dict(), sort_keys=True).encode("utf8")
            )
            if new_hash.hexdigest() != self._rd_hash:
                # only set input if the result definition changed
                self._operator.inputs.result_definition(self.result_definition.to_json())
                self._isuptodate = False
                self._rd_hash = new_hash.hexdigest()
        else:
            raise RuntimeError(
                "Cannot update sampling point because the result definition is missing."
            )

        result_as_string = self._operator.outputs.results()
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
        if not self._isuptodate or not self._results:
            self.run()

        ply_wise_indices = [self._interface_indices[v] for v in spots]
        ply_wise_indices.sort()
        indices = []
        if self.analysis_plies:
            for ply_index in range(0, self.number_of_plies):
                indices.extend(
                    [ply_index * self._spots_per_ply + index for index in ply_wise_indices]
                )

        return indices

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
        offsets = self.offsets
        indices = self.get_indices(spots)

        if core_scale_factor == 1.0:
            return cast(npt.NDArray[np.float64], offsets[indices])

        thicknesses = []
        if not self.analysis_plies:
            raise RuntimeError("No analysis plies are found in the selected element.")

        for index, ply in enumerate(self.analysis_plies):
            is_core = ply["is_core"]
            # get thickness from the offsets
            th = (
                offsets[(index + 1) * self._spots_per_ply - 1]
                - offsets[index * self._spots_per_ply]
            )
            if is_core:
                th *= core_scale_factor

            thicknesses.append(th)

        for index, ply in enumerate(self.analysis_plies):
            # spots per ply is always 2 or 3
            step = thicknesses[index] / (self._spots_per_ply - 1)
            top_of_previous_ply = (
                offsets[index * self._spots_per_ply - 1] if index > 0 else offsets[0]
            )
            for i in range(0, self._spots_per_ply):
                offsets[index * self._spots_per_ply + i] = top_of_previous_ply + step * i

        return cast(npt.NDArray[np.float64], offsets[indices])

    def get_ply_wise_critical_failures(self) -> List[FailureResult]:
        """Get the critical failure value and modes per ply."""
        num_plies = self.number_of_plies

        irfs = self.inverse_reserve_factor.reshape(num_plies, self._spots_per_ply)
        mos = self.margin_of_safety.reshape(num_plies, self._spots_per_ply)
        rfs = self.reserve_factor.reshape(num_plies, self._spots_per_ply)
        failure_models = np.array(self.failure_modes).reshape(num_plies, self._spots_per_ply)

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
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")

        theta = np.array(self._results[0]["layup"]["polar_properties"]["angles"]) / 180.0 * np.pi
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"})

        for comp in components:
            ax.plot(theta, getattr(self, f"polar_properties_{comp}", []), label=comp)

        ax.set_title("Polar Properties")
        ax.legend()
        return SamplingPointFigure(fig, ax)

    def add_ply_sequence_to_plot(self, axes: Any, core_scale_factor: float = 1.0) -> None:
        """Add the stacking (ply and text) to an axis or plot.

        Parameters
        ----------
        axes :
            Matplotlib :py:class:`~matplotlib.axes.Axes` object.
        core_scale_factor :
            Factor for scaling the thickness of core plies.
        """
        offsets = self.get_offsets_by_spots(
            spots=[Spot.BOTTOM, Spot.TOP], core_scale_factor=core_scale_factor
        )

        if len(offsets) == 0:
            return

        num_spots = 2
        axes.set_ybound(offsets[0], offsets[-1])
        x_bound = axes.get_xbound()
        width = x_bound[1] - x_bound[0]

        for index, ply in enumerate(self.analysis_plies):
            angle = float(ply["angle"])
            hatch = "x" if ply["is_core"] else ""

            height = offsets[(index + 1) * num_spots - 1] - offsets[index * num_spots]
            origin = (x_bound[0], offsets[index * num_spots])
            axes.add_patch(
                Rectangle(xy=origin, width=width, height=height, fill=False, hatch=hatch)
            )
            mat = ply["material"]
            th = float(ply["thickness"])
            text = f"{mat}\nangle={angle:.3}, th={th:.3}"
            axes.annotate(
                text=text,
                xy=(origin[0] + width / 2.0, origin[1] + height / 2.0),
                ha="center",
                va="center",
                fontsize=8,
            )

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
        indices = self.get_indices(spots)
        offsets = self.get_offsets_by_spots(spots, core_scale_factor)

        for comp in components:
            raw_values = getattr(self, comp)
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

    def get_result_plots(
        self,
        strain_components: Sequence[str] = ("e1", "e2", "e3", "e12", "e13", "e23"),
        stress_components: Sequence[str] = ("s1", "s2", "s3", "s12", "s13", "s23"),
        failure_components: Sequence[FailureMeasure] = (
            FailureMeasure.INVERSE_RESERVE_FACTOR,
            FailureMeasure.RESERVE_FACTOR,
            FailureMeasure.MARGIN_OF_SAFETY,
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
                    raise RuntimeError(
                        f"{type(axes_obj).__name__} plot cannot be indexed."
                    ) from exc
                return axes_obj
            except IndexError as exc:
                raise RuntimeError("get_subplot: index exceeds limit.") from exc

        if num_active_plots > 0:
            ticks = self.get_offsets_by_spots(spots=[Spot.TOP], core_scale_factor=core_scale_factor)

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
                self.add_ply_sequence_to_plot(layup_axis, core_scale_factor)
                layup_axis.set_xticks([])
                axes_index += 1

                plt.rcParams["hatch.linewidth"] = 1.0
                plt.rcParams["hatch.color"] = "black"

            if len(strain_components) > 0:
                strain_axis = _get_subplot(axes, axes_index)
                self.add_results_to_plot(
                    strain_axis, strain_components, spots, core_scale_factor, "Strains", "[-]"
                )
                axes_index += 1

            if len(stress_components) > 0:
                stress_axis = _get_subplot(axes, axes_index)
                self.add_results_to_plot(
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
                internal_fc = [self._FAILURE_MODE_NAMES_TO_ACP[v] for v in failure_components]
                self.add_results_to_plot(
                    failure_axis, internal_fc, spots, core_scale_factor, "Failures", "[-]"
                )

                if show_failure_modes:
                    middle_offsets = self.get_offsets_by_spots(
                        spots=[Spot.MIDDLE], core_scale_factor=core_scale_factor
                    )
                    critical_failures = self.get_ply_wise_critical_failures()

                    if len(critical_failures) != len(middle_offsets):
                        raise IndexError("Sizes of failures and offsets do not match.")

                    for index, offset in enumerate(middle_offsets):
                        for fc in failure_components:
                            failure_axis.annotate(
                                getattr(critical_failures[index], "mode"),
                                xy=(getattr(critical_failures[index], fc.value), offset),
                                xytext=(getattr(critical_failures[index], fc.value), offset),
                            )

                axes_index += 1

        return SamplingPointFigure(fig, axes)

    def _update_and_check_results(self) -> None:
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")
