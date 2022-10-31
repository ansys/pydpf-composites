"""Wrapper for the Sampling Point Operator"""

import json
#from typing import Any, Dict, Sequence
import matplotlib.pyplot as plt
import numpy as np

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

    #todo: should we support the different server types if server is None?

    def __init__(
        self,
        name: str,
        result_definition: ResultDefinition = None,
        server: BaseServer = None
    ):
        """Create a SamplingPoint object."""
        self.name = name
        self._result_definition = result_definition

        #todo: TBD - how to handle the server

        #specifies the server. Creates a new one if needed
        self._server = get_or_create_server(server)
        if not self._server:
            raise RuntimeError("SamplingPoint: cannot connect or create a server")

        load_composites_plugin()

        #initialize the sampling point operator. Do it just once
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
    def inverse_reserve_factors(self):
        if self._uptodate and self._results:
            return self._results[0]["results"]["failures"]["inverse_reserve_factor"]

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

    def plot(self,
             show_failure_modes: bool = False):
        """Plots all results.
        """

        offsets = self.offsets

        fig = plt.figure()
        gs = fig.add_gridspec(1, 3, hspace=0, wspace=0)
        (strains, stresses, failures) = gs.subplots(sharex='col', sharey='row')

        strains.plot(self.e1, offsets, label="e1")
        strains.plot(self.e2, offsets, label="e2")
        strains.plot(self.e12, offsets, label="e12")
        strains.plot(self.e13, offsets, label="e13")
        strains.plot(self.e23, offsets, label="e23")
        strains.set_title("Strains")
        strains.legend()
        strains.grid()

        stresses.plot(self.s1, offsets, label="s1")
        stresses.plot(self.s2, offsets, label="s2")
        stresses.plot(self.s3, offsets, label="s3")
        stresses.plot(self.s12, offsets, label="s12")
        stresses.plot(self.s13, offsets, label="s13")
        stresses.plot(self.s23, offsets, label="s23")
        stresses.set_title("Stresses")
        stresses.grid()

        irfs = self.inverse_reserve_factors
        failures.plot(irfs, offsets, label="irf")
        failures.set_title("Failures")
        if show_failure_modes:
            fms = self.failure_modes
            for index, fm in enumerate(fms):
                failures.annotate(fms[index],
                                  xy=(irfs[index], offsets[index]),
                                  xytext=(irfs[index], offsets[index])
                                  )

        failures.legend()
        failures.grid()

        angles_in_rad = np.array(self._results[0]["layup"]["polar_properties"]["angles"])/180.*np.pi

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ax.plot(angles_in_rad, self.polar_properties_E1, label="E1")
        ax.plot(angles_in_rad, self.polar_properties_E2, label="E2")
        ax.plot(angles_in_rad, self.polar_properties_G12, label="G12")
        ax.legend()

        plt.show()