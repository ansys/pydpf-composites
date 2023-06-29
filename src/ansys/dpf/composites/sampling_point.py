"""Wrapper for the sampling point operator."""
import hashlib
import json
from typing import Any, Collection, Sequence, Union

import ansys.dpf.core as dpf
from ansys.dpf.core.server_types import BaseServer
import numpy as np
import numpy.typing as npt

from ._sampling_point_base import SamplingPointBase, SamplingPointFigure
from .constants import Spot
from .result_definition import FailureMeasure, ResultDefinition


class SamplingPoint(SamplingPointBase):
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
        result_definition.check_has_single_scope(f"Sampling point {name} cannot be created.")

        super().__init__(name, server)
        self._result_definition = result_definition

        # initialize the sampling point operator. Do it just once
        self._operator = dpf.Operator(
            name="composite::composite_sampling_point_operator", server=self._server
        )
        if not self._operator:
            raise RuntimeError("SamplingPoint: failed to initialize the operator.")

    @property
    def result_definition(self) -> ResultDefinition:
        """Input for the sampling point operator."""
        return self._result_definition

    @result_definition.setter
    def result_definition(self, value: ResultDefinition) -> None:
        value.check_has_single_scope(
            f"Result definition of Sampling point {self.name}" " cannot be set."
        )
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
        return super().analysis_plies

    @property
    def s1(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 1 direction of each ply."""
        self._update_and_check_results()
        return super().s1

    @property
    def s2(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 2 direction of each ply."""
        self._update_and_check_results()
        return super().s2

    @property
    def s3(self) -> npt.NDArray[np.float64]:
        """Stresses in the material 3 direction of each ply."""
        self._update_and_check_results()
        return np.array(self._results[0]["results"]["stresses"]["s3"])

    @property
    def s12(self) -> npt.NDArray[np.float64]:
        """In-plane shear stresses s12 of each ply."""
        self._update_and_check_results()
        return super().s12

    @property
    def s13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s13 of each ply."""
        self._update_and_check_results()
        return super().s13

    @property
    def s23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear stresses s23 of each ply."""
        self._update_and_check_results()
        return super().s23

    @property
    def e1(self) -> npt.NDArray[np.float64]:
        """Strains in the material 1 direction of each ply."""
        self._update_and_check_results()
        return super().e1

    @property
    def e2(self) -> npt.NDArray[np.float64]:
        """Strains in the material 2 direction of each ply."""
        self._update_and_check_results()
        return super().e2

    @property
    def e3(self) -> npt.NDArray[np.float64]:
        """Strains in the material 3 direction of each ply."""
        self._update_and_check_results()
        return super().e3

    @property
    def e12(self) -> npt.NDArray[np.float64]:
        """In-plane shear strains e12 of each ply."""
        self._update_and_check_results()
        return super().e12

    @property
    def e13(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e13 of each ply."""
        self._update_and_check_results()
        return super().e13

    @property
    def e23(self) -> npt.NDArray[np.float64]:
        """Out-of-plane shear strains e23 of each ply."""
        self._update_and_check_results()
        return super().e23

    @property
    def inverse_reserve_factor(self) -> npt.NDArray[np.float64]:
        """Critical inverse reserve factor of each ply."""
        self._update_and_check_results()
        return super().inverse_reserve_factor

    @property
    def reserve_factor(self) -> npt.NDArray[np.float64]:
        """Lowest reserve factor of each ply.

        This attribute is equivalent to the safety factor.
        """
        self._update_and_check_results()
        return super().reserve_factor

    @property
    def margin_of_safety(self) -> npt.NDArray[np.float64]:
        """Lowest margin of safety of each ply.

        This attribute is equivalent to the safety margin.
        """
        self._update_and_check_results()
        return super().margin_of_safety

    @property
    def failure_modes(self) -> Sequence[str]:
        """Critical failure mode of each ply."""
        self._update_and_check_results()
        return super().failure_modes

    @property
    def offsets(self) -> npt.NDArray[np.float64]:
        """Z coordinates for each interface and ply."""
        self._update_and_check_results()
        return super().offsets

    @property
    def polar_properties_E1(self) -> npt.NDArray[np.float64]:
        """Polar property E1 of the laminate."""
        self._update_and_check_results()
        return super().polar_properties_E1

    @property
    def polar_properties_E2(self) -> npt.NDArray[np.float64]:
        """Polar property E2 of the laminate."""
        self._update_and_check_results()
        return super().polar_properties_E2

    @property
    def polar_properties_G12(self) -> npt.NDArray[np.float64]:
        """Polar property G12 of the laminate."""
        self._update_and_check_results()
        return super().polar_properties_G12

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
        self._update_and_check_results()
        return super().get_indices(spots)

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
        super().get_polar_plot(components)

    def _update_and_check_results(self) -> None:
        if not self._isuptodate or not self._results:
            self.run()

        if not self._results:
            raise RuntimeError(f"Results of sampling point {self.name} are not available.")
