"""Wrapper for the Sampling Point Operator"""

import json
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from typing import Sequence

from .result_definition import ResultDefinition
from .load_plugin import load_composites_plugin

import ansys.dpf.core as dpf
from ansys.dpf.core.server_types import BaseServer
from ansys.dpf.core.server import get_or_create_server


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

    FAILURE_MODES = {"irf": "inverse_reserve_factor",
                     "rf": "reserve_factor",
                     "mos": "margin_of_safety"}

    # todo: should we support the different server types if server is None?

    def __init__(
            self,
            name: str,
            result_definition: ResultDefinition = None,
            server: BaseServer = None
    ):
        """Create a SamplingPoint object."""
        self.name = name
        self._result_definition = result_definition

        # todo: TBD - how to handle the server

        # specifies the server. Creates a new one if needed
        self._server = get_or_create_server(server)
        if not self._server:
            raise RuntimeError("SamplingPoint: cannot connect or create a server")

        load_composites_plugin()

        # initialize the sampling point operator. Do it just once
        self._operator = dpf.Operator(name="composite::composite_sampling_point_operator", server=server)
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
    def server(self):
        return self._server

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
            return self._results[0]["results"]["stresses"]["s1"]

    @property
    def s2(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["stresses"]["s2"]

    @property
    def s3(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["stresses"]["s3"]

    @property
    def s12(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["stresses"]["s12"]

    @property
    def s13(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["stresses"]["s13"]

    @property
    def s23(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["stresses"]["s23"]

    @property
    def e1(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e1"]

    @property
    def e2(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e2"]

    @property
    def e3(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e3"]

    @property
    def e12(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e12"]

    @property
    def e13(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e13"]

    @property
    def e23(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["strains"]["e23"]

    @property
    def inverse_reserve_factor(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["failures"]["inverse_reserve_factor"]

    @property
    def reserve_factor(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["failures"]["reserve_factor"]

    @property
    def margin_of_safety(self):
        if self._uptodate and self._results:
            return self._results[0]['results']['failures']['margin_of_safety']

    @property
    def failure_modes(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["failures"]["failure_modes"]

    @property
    def offsets(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["offsets"]

    @property
    def polar_properties_E1(self):
        if self._uptodate and self._results:
            return self._results[0]["layup"]["polar_properties"]["E1"]

    @property
    def polar_properties_E2(self):
        if self._uptodate and self._results:
            return self._results[0]["layup"]["polar_properties"]["E2"]

    @property
    def polar_properties_G12(self):
        if self._uptodate and self._results:
            return self._results[0]["layup"]["polar_properties"]["G12"]

    def update(self):
        """ Updates the results
        """
        self._operator.inputs.result_definition(self.result_definition.to_json())
        result_as_string = self._operator.outputs.results()
        self._results = json.loads(result_as_string)
        self._uptodate = True

    def _plot_yaxis_data(self, core_scale_factor):
        # returns the offsets and ticks of the y-axis
        offsets = np.array(self.offsets)
        for index, ply in enumerate(self.analysis_plies):
            is_core = ply["is_core"]
            height = offsets[index * 3 + 2] - offsets[index * 3]
            if is_core:
                height *= core_scale_factor

            if index > 0:
                # top of previous ply is bottom of current ply
                offsets[index * 3] = offsets[index * 3 - 1]

            offsets[index * 3 + 1] = offsets[index * 3] + height / 2.
            offsets[index * 3 + 2] = offsets[index * 3] + height

        ticks = list(offsets[::3]) + [offsets[-1]]

        return offsets, ticks

    def _polar_plot(self):
        # adds a polar plot of the laminate properties
        angles_in_rad = np.array(self._results[0]["layup"]["polar_properties"]["angles"]) / 180. * np.pi

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ax.plot(angles_in_rad, self.polar_properties_E1, label="E1")
        ax.plot(angles_in_rad, self.polar_properties_E2, label="E2")
        ax.plot(angles_in_rad, self.polar_properties_G12, label="G12")
        ax.legend()
        return fig, ax

    def _laminate_plot(self, plot, offsets):
        width = 1.
        for index, ply in enumerate(self.analysis_plies):
            angle = ply["angle"]
            sinus = np.sin(angle / 180. * np.pi)
            hatch = ""

            if ply["is_core"]:
                hatch = "x"
            #elif np.sin(-np.pi / 8) < sinus < np.sin(np.pi / 8):
            #    hatch = "--"
            #elif np.sin(np.pi / 8) < sinus < np.sin(3 * np.pi / 8):
            #    hatch = "/"
            #elif np.sin(3 * np.pi / 8) < sinus < np.sin(5 * np.pi / 8):
            #    hatch = "|"
            #elif np.sin(-3 * np.pi / 8) < sinus < np.sin(-np.pi / 8):
            #    hatch = "\\"

            height = offsets[index * 3 + 2] - offsets[index * 3]
            origin = (0., offsets[index * 3])
            plot.add_patch(Rectangle(
                xy=origin,
                width=width,
                height=height,
                fill=False,
                hatch=hatch
            ))
            mat = ply["material"]
            th = ply["thickness"]
            text = f"{mat}\nangle={angle}, th={th}"
            plot.annotate(text=text,
                          xy=(origin[0] + width / 2., origin[1] + height / 2.),
                          ha="center",
                          va="center",
                          fontsize=8)

    def _component_plot(self, plot, offsets, components, title):
        for comp in components:
            plot.plot(getattr(self, comp), offsets, label=comp)
        plot.set_title(title)
        plot.legend()
        plot.grid()

    def plot(self,
             strain_components: Sequence[str] = ["e1", "e2", "e3", "e12", "e13", "e23"],
             stress_components: Sequence[str] = ["s1", "s2", "s3", "s12", "s13", "s23"],
             failure_components: Sequence[str] = ["irf", "rf", "mos"],
             show_failure_modes: bool = False,
             show_laminate: bool = True,
             show_polar_plot: bool = True,
             core_scale_factor: float = 1.):
        """Plots all results.
        """

        offsets, ticks = self._plot_yaxis_data(core_scale_factor)
        num_active_plots = int(show_laminate)
        num_active_plots += 1 if len(strain_components) > 0 else 0
        num_active_plots += 1 if len(stress_components) > 0 else 0
        num_active_plots += 1 if len(failure_components) > 0 else 0

        fig = plt.figure()
        gs = fig.add_gridspec(1, num_active_plots, hspace=0, wspace=0)
        sub_plots = gs.subplots(sharex='col', sharey='row')

        if num_active_plots > 0:
            if core_scale_factor != 1.:
                labels = []
            else:
                labels = [str(t) for t in ticks]

            sub_plots[0].set_yticks(ticks=ticks, labels=labels)

            index = 0
            if show_laminate:
                self._laminate_plot(sub_plots[index], offsets)
                index += 1

            if len(strain_components) > 0:
                self._component_plot(sub_plots[index], offsets, strain_components, "Strains")
                index += 1

            if len(stress_components) > 0:
                self._component_plot(sub_plots[index], offsets, stress_components, "Stresses")
                index += 1

            if len(failure_components) > 0:

                failure_plot = sub_plots[index]
                failure_components = [self.FAILURE_MODES[v] for v in failure_components]
                self._component_plot(failure_plot, offsets, failure_components, "Failures")

                all_measures = [getattr(self, v) for v in failure_components]

                if show_failure_modes:
                    modes = self.failure_modes
                    for index, fm in enumerate(modes):
                        for values in all_measures:
                            failure_plot.annotate(fm,
                                                  xy=(values[index], offsets[index]),
                                                  xytext=(values[index], offsets[index])
                                                  )

                index += 1

        if show_polar_plot:
            fix, polar_plot = self._polar_plot()

        plt.show()
