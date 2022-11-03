"""Wrapper for the Sampling Point Operator"""

import json
from typing import Sequence

import ansys.dpf.core as dpf
from ansys.dpf.core.server import get_or_create_server
from ansys.dpf.core.server_types import BaseServer
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np

from .load_plugin import load_composites_plugin
from .result_definition import ResultDefinition


class SamplingPoint:
    """Implements the Sampling Point object which uses the sampling point operator
    of dpf-composites. Allows to plot the lay-up and results at a certain point of the
    layerd structure.

    Parameters
    ----------
    name :
        The name of the object.
    result_definition :
        Result definition object which defines all the inputs and scope.
    """

    FAILURE_MODES = {
        "irf": "inverse_reserve_factor",
        "rf": "reserve_factor",
        "mos": "margin_of_safety",
    }

    # todo: should we support the different server types if server is None?

    def __init__(
        self, name: str, result_definition: ResultDefinition = None, server: BaseServer = None
    ):
        """Create a SamplingPoint object."""
        self._spots_per_ply = 0
        self._interface_indices = {}
        self.name = name
        self._result_definition = result_definition

        # todo: TBD - how to handle the server

        # specifies the server. Creates a new one if needed
        used_server = get_or_create_server(server)
        if not used_server:
            raise RuntimeError("SamplingPoint: cannot connect to DPF server or launch it.")

        if used_server != server:
            load_composites_plugin()

        # initialize the sampling point operator. Do it just once
        self._operator = dpf.Operator(
            name="composite::composite_sampling_point_operator", server=used_server
        )
        if not self._operator:
            raise RuntimeError("SamplingPoint: failed to initialize the operator!")

        self._results = None
        self._uptodate = False

    @property
    def result_definition(self):
        return self._result_definition

    @result_definition.setter
    def result_definition(self, value):
        self._uptodate = False
        self._result_definition = value

    @property
    def results(self):
        if self._uptodate and self._results:
            return self._results

    @property
    def analysis_plies(self):
        if self._uptodate and self._results:
            return self._results[0]["layup"]["analysis_plies"]

    @property
    def s1(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s1"])

    @property
    def s2(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s2"])

    @property
    def s3(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s3"])

    @property
    def s12(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s12"])

    @property
    def s13(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s13"])

    @property
    def s23(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["stresses"]["s23"])

    @property
    def e1(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e1"])

    @property
    def e2(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e2"])

    @property
    def e3(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e3"])

    @property
    def e12(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e12"])

    @property
    def e13(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e13"])

    @property
    def e23(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["strains"]["e23"])

    @property
    def inverse_reserve_factor(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["failures"]["inverse_reserve_factor"])

    @property
    def reserve_factor(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["failures"]["reserve_factor"])

    @property
    def margin_of_safety(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["failures"]["margin_of_safety"])

    @property
    def failure_modes(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["failures"]["failure_modes"])

    @property
    def offsets(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["results"]["offsets"])

    @property
    def polar_properties_E1(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["layup"]["polar_properties"]["E1"])

    @property
    def polar_properties_E2(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["layup"]["polar_properties"]["E2"])

    @property
    def polar_properties_G12(self):
        if self._uptodate and self._results:
            return np.array(self._results[0]["layup"]["polar_properties"]["G12"])

    def update(self):
        """Query the results from the DPF operator and updates the local copy of the results"""
        self._operator.inputs.result_definition(self.result_definition.to_json())
        result_as_string = self._operator.outputs.results()
        self._results = json.loads(result_as_string)

        # update the number of spots
        self._spots_per_ply = int(
            len(np.array(self._results[0]["results"]["strains"]["e1"]))
            / len(self._results[0]["layup"]["analysis_plies"])
        )

        if self._spots_per_ply == 3:
            self._interface_indices = {"bottom": 0, "middle": 1, "top": 2}
        elif self._spots_per_ply == 2:
            self._interface_indices = {"bottom": 0, "top": 1}
        elif self._spots_per_ply == 1:
            self._interface_indices = {"middle": 0}

        self._uptodate = True

    def get_indices(self, spots: Sequence[str] = ["bottom", "middle", "top"]):
        """Returns the indices of the selected interfaces for each ply.
        The indices are sorted from bottom to top.
        For instance, can be used to access the stresses at the bottom of each ply.

        Parameters
        ----------
        spots
            selection of the interfaces. Only the indices of the bottom interfaces of plies
            are returned if spots is equal to ["bottom"]
        """
        ply_wise_indices = [self._interface_indices[v] for v in spots]
        ply_wise_indices.sort()
        num_plies = len(self.analysis_plies)

        indices = []
        for ply_index in range(0, num_plies):
            indices.extend([ply_index * self._spots_per_ply + index for index in ply_wise_indices])

        return indices

    def get_offsets(
        self, spots: Sequence[str] = ["bot", "mid", "top"], core_scale_factor: float = 1.0
    ):
        """Returns the y coordinates of the selected interfaces for each ply.
        Core materials can be scaled by core_scale_factor

        Parameters
        ----------
        spots:
            Select the interfaces of interest

        core_scale_factor:
            Scale the thickness of core plies
        """
        offsets = self.offsets
        indices = self.get_indices(spots)

        if core_scale_factor == 1.0:
            return offsets[indices]

        thicknesses = []
        for index, ply in enumerate(self.analysis_plies):
            is_core = ply["is_core"]

            if self._spots_per_ply > 1:
                # get thickness from the offsets
                th = (
                    offsets[(index + 1) * self._spots_per_ply - 1]
                    - offsets[index * self._spots_per_ply]
                )
            else:
                # get thickness from the analysis ply
                th = ply["thickness"]

            if is_core:
                th *= core_scale_factor

            thicknesses.append(th)

        for index, ply in enumerate(self.analysis_plies):
            if self._spots_per_ply > 1:
                step = thicknesses[index] / (self._spots_per_ply - 1)
                top_of_previous_ply = (
                    offsets[index * self._spots_per_ply - 1] if index > 0 else offsets[0]
                )
                for i in range(0, self._spots_per_ply):
                    offsets[index * self._spots_per_ply + i] = top_of_previous_ply + step * i
            else:
                # spots_per_ply is 1
                if index == 0:
                    offsets[0] = self.results[0]["layup"]["offset"] + th / 2.0
                else:
                    offsets[index] = (
                        offsets[index - 1] + (thicknesses[index - 1] + thicknesses[index]) / 2.0
                    )

        return offsets[indices]

    def get_polar_plot(self, components: Sequence[str] = ["E1", "E2", "G12"]):
        """Returns the figure and axis of the default polar plot

        Parameters
        ----------
        components :
            Defines which stiffness quantities should be added to the plot

        Example
        -------
        sampling_point.get_polar_plot(components=["E1", "G12"])
        """
        theta = np.array(self._results[0]["layup"]["polar_properties"]["angles"]) / 180.0 * np.pi
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"})

        for comp in components:
            ax.plot(theta, getattr(self, f"polar_properties_{comp}", []), label=comp)

        ax.set_title("Polar Properties")
        ax.legend()
        return fig, ax

    def add_ply_sequence_to_plot(self, axis, core_scale_factor):
        """This function adds the stacking (ply + text) to an axis/plot.

        Parameters
        ----------
        axis
            Matplotlib plot/axis object
        core_scale_factor
            Scales the thickness of core plies
        """
        offsets = self.get_offsets(spots=["bottom", "top"], core_scale_factor=core_scale_factor)

        num_spots = 2
        x_bound = axis.get_xbound()
        width = x_bound[1] - x_bound[0]

        for index, ply in enumerate(self.analysis_plies):
            angle = ply["angle"]
            hatch = "x" if ply["is_core"] else ""

            height = offsets[(index + 1) * num_spots - 1] - offsets[index * num_spots]
            origin = (x_bound[0], offsets[index * num_spots])
            axis.add_patch(
                Rectangle(xy=origin, width=width, height=height, fill=False, hatch=hatch)
            )
            mat = ply["material"]
            th = ply["thickness"]
            text = f"{mat}\nangle={angle}, th={th}"
            axis.annotate(
                text=text,
                xy=(origin[0] + width / 2.0, origin[1] + height / 2.0),
                ha="center",
                va="center",
                fontsize=8,
            )

    def add_results_to_plot(self, axis, components, spots, core_scale_factor, title):
        """Add results (strains, stresses or failure values) to a plot/axis."""
        indices = self.get_indices(spots)
        offsets = self.get_offsets(spots, core_scale_factor)

        for comp in components:
            raw_values = getattr(self, comp)
            values = [raw_values[i] for i in indices]
            axis.plot(values, offsets, label=comp)
        if title:
            axis.set_title(title)
        axis.legend()
        axis.grid()

    def get_result_plots(
        self,
        strain_components: Sequence[str] = ["e1", "e2", "e3", "e12", "e13", "e23"],
        stress_components: Sequence[str] = ["s1", "s2", "s3", "s12", "s13", "s23"],
        failure_components: Sequence[str] = ["irf", "rf", "mos"],
        show_failure_modes: bool = False,
        show_laminate: bool = True,
        core_scale_factor: float = 1.0,
        spots=["bottom", "middle", "top"],
    ):
        """Returns a figure with an axis (plot) for each selected result entity.

        Parameters:
        -----------
        """

        num_active_plots = int(show_laminate)
        num_active_plots += 1 if len(strain_components) > 0 else 0
        num_active_plots += 1 if len(stress_components) > 0 else 0
        num_active_plots += 1 if len(failure_components) > 0 else 0

        fig = plt.figure()
        gs = fig.add_gridspec(1, num_active_plots, hspace=0, wspace=0)
        axes = gs.subplots(sharex="col", sharey="row")

        if num_active_plots > 0:
            ticks = self.get_offsets(spots=["top"], core_scale_factor=core_scale_factor)

            if core_scale_factor != 1.0:
                labels = []
            else:
                labels = [str(t) for t in ticks]

            axes[0].set_yticks(ticks=ticks, labels=labels)

            index = 0
            if show_laminate:
                plt.rcParams["hatch.linewidth"] = 0.2
                self.add_ply_sequence_to_plot(axes[index], core_scale_factor)
                axes[index].set_xticks([])
                index += 1

            if len(strain_components) > 0:
                self.add_results_to_plot(
                    axes[index], strain_components, spots, core_scale_factor, "Strains"
                )
                index += 1

            if len(stress_components) > 0:
                self.add_results_to_plot(
                    axes[index], stress_components, spots, core_scale_factor, "Stresses"
                )
                index += 1

            if len(failure_components) > 0:

                failure_plot = axes[index]
                failure_components = [self.FAILURE_MODES[v] for v in failure_components]
                self.add_results_to_plot(
                    axes[index], failure_components, spots, core_scale_factor, "Failures"
                )

                # todo: extract the failure mode of the critical value and move to a separate function
                middle_indices = self.get_indices(["middle"])
                middle_offsets = self.get_offsets(
                    spots=["middle"], core_scale_factor=core_scale_factor
                )
                all_measures = [
                    np.array(getattr(self, v))[middle_indices] for v in failure_components
                ]

                if show_failure_modes:
                    raw_data = self.failure_modes
                    modes = [raw_data[i] for i in middle_indices]
                    for index, fm in enumerate(modes):
                        for values in all_measures:
                            failure_plot.annotate(
                                fm,
                                xy=(values[index], middle_offsets[index]),
                                xytext=(values[index], middle_offsets[index]),
                            )

                index += 1

        return fig, axes
