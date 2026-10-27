# Copyright (C) 2022 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Immutable inputs and results for fixed-resultant laminate optimization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from math import isclose, isfinite
from numbers import Integral
from types import MappingProxyType
from typing import Any


def _finite(value: float, name: str, *, positive: bool = False) -> None:
    if not isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive." if positive else "."))


@dataclass(frozen=True)
class Material:
    """Material definition, resolved by name publicly and external ID in DPF.

    ``properties`` uses the CLT schema names (E1, E2, ..., nu23, or E and nu
    for isotropic materials). Density and allowables come from the DPF materials
    container, not this dictionary. All properties must use the laminate units.
    """

    name: str
    external_id: str
    ply_type: str
    properties: Mapping[str, float]
    nominal_thickness: float | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.external_id:
            raise ValueError("Material name and external ID must not be empty.")
        isotropic = self.ply_type in ("isotropic", "isotropic_homogeneous_core", "undefined")
        allowed = {"regular", "woven", "honeycomb_core", "orthotropic_homogeneous_core", "adhesive"}
        if not isotropic and self.ply_type not in allowed:
            raise ValueError(f"Unsupported material type: {self.ply_type}")
        required = (
            ("E", "nu")
            if isotropic
            else ("E1", "E2", "E3", "G12", "G13", "G23", "nu12", "nu13", "nu23")
        )
        if set(self.properties) != set(required):
            raise ValueError(f"Material {self.name!r} requires exactly {required}.")
        for name, value in self.properties.items():
            _finite(value, name, positive=name.startswith(("E", "G")))
        object.__setattr__(self, "properties", MappingProxyType(dict(self.properties)))
        if self.nominal_thickness is not None:
            _finite(self.nominal_thickness, "nominal_thickness", positive=True)

    @property
    def is_core(self) -> bool:
        """Whether this material is a sandwich core."""
        return self.ply_type in (
            "honeycomb_core",
            "orthotropic_homogeneous_core",
            "isotropic_homogeneous_core",
        )

    def to_clt_dict(self) -> dict[str, Any]:
        """Return a CLT schema material definition."""
        return {
            "name": self.name,
            "id": self.name,
            "ext_id": self.external_id,
            "type": self.ply_type,
            "properties": dict(self.properties),
        }


@dataclass(frozen=True)
class Ply:
    """One local ply occurrence with preserved ACP/DPF source identifiers.

    ``global_ply_number`` retains the source analysis-ply number, including after
    reordering. The tuple position defines the candidate's actual local order.
    None is permitted for manually defined plies without source metadata.
    New optimization plies receive provisional numbers, not final ACP ranks.
    """

    id: str
    material: str
    angle: float
    thickness: float
    global_ply_number: int | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.material:
            raise ValueError("Ply ID and material must not be empty.")
        _finite(self.angle, "angle")
        _finite(self.thickness, "thickness", positive=True)
        if self.global_ply_number is not None:
            if (
                isinstance(self.global_ply_number, bool)
                or not isinstance(self.global_ply_number, Integral)
                or self.global_ply_number < 0
            ):
                raise ValueError("global_ply_number must be a nonnegative integer or None.")
            object.__setattr__(self, "global_ply_number", int(self.global_ply_number))


@dataclass(frozen=True)
class LaminateForces:
    """Resultants in the fixed local frame: force/length and moment/length.

    Moments are about the unchanged reference plane z=0. Changing a laminate
    offset does not redefine that plane. Use the same units as the laminate.
    """

    Nx: float = 0.0
    Ny: float = 0.0
    Nxy: float = 0.0
    Mx: float = 0.0
    My: float = 0.0
    Mxy: float = 0.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            _finite(value, name)


@dataclass(frozen=True)
class LoadCase:
    """Named resultants for one sampling point in that point's local frame."""

    name: str
    forces: LaminateForces

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Load-case name must not be empty.")


@dataclass(frozen=True)
class Laminate:
    """Complete local stack, ordered bottom-to-top, with fixed load cases.

    Names and ply IDs must be qualified by the caller when combining multiple
    ACP models or composite definitions. ``weight`` represents area or an
    explicitly chosen sampling weight; equal weights do not imply total mass.
    """

    name: str
    plies: tuple[Ply, ...]
    materials: tuple[Material, ...]
    load_cases: tuple[LoadCase, ...]
    unit_system: str
    offset: float = 0.0
    element_id: int = 0
    weight: float = 1.0

    def __post_init__(self) -> None:
        for name in ("plies", "materials", "load_cases"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if not self.name or not self.unit_system or not self.plies or not self.load_cases:
            raise ValueError("Laminate needs a name, units, at least one ply and one load case.")
        for values, label in (
            ([p.id for p in self.plies], "ply IDs"),
            ([m.name for m in self.materials], "material names"),
            ([c.name for c in self.load_cases], "load-case names"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate {label} in {self.name!r}.")
        if {p.material for p in self.plies} - {m.name for m in self.materials}:
            raise ValueError(f"Unresolved ply material in {self.name!r}.")
        _finite(self.offset, "offset")
        _finite(self.weight, "weight", positive=True)

    @property
    def thickness(self) -> float:
        """Total laminate thickness."""
        return sum(p.thickness for p in self.plies)

    def is_symmetric(self, tolerance: float = 1e-8) -> bool:
        """Check material, thickness and angle reflection, not +/- angle balance."""
        for bottom, top in zip(self.plies, reversed(self.plies)):
            angle_difference = (bottom.angle - top.angle + 90) % 180 - 90
            if (
                bottom.material != top.material
                or not isclose(bottom.thickness, top.thickness, rel_tol=tolerance, abs_tol=0)
                or abs(angle_difference) > tolerance
            ):
                return False
        return True

    def to_clt_dict(self, load_case: LoadCase) -> dict[str, Any]:
        """Build a fresh input document without mutating the source sampling point."""
        catalog = {m.name: m for m in self.materials}
        # Only manually created plies without source metadata need a temporary
        # schema value. Never renumber an existing source or added-ply number.
        next_number = (
            max(
                (p.global_ply_number for p in self.plies if p.global_ply_number is not None),
                default=0,
            )
            + 1
        )
        global_numbers = {}
        for ply in self.plies:
            number = ply.global_ply_number
            if number is None:
                number = next_number
                next_number += 1
            global_numbers[ply.id] = number
        return {
            "element_label": self.element_id,
            "element_type": "shell",
            "unit_system": self.unit_system,
            "materials": [m.to_clt_dict() for m in self.materials],
            "layup": {
                "offset": self.offset,
                "num_analysis_plies": len(self.plies),
                "analysis_plies": [
                    {
                        **asdict(p),
                        "global_ply_number": global_numbers[p.id],
                        "is_core": catalog[p.material].is_core,
                    }
                    for p in self.plies
                ],
            },
            "laminate_forces": asdict(load_case.forces),
        }

    @classmethod
    def from_sampling_point(
        cls,
        sampling_point: Any,
        *,
        name: str | None = None,
        load_cases: Sequence[LoadCase] | None = None,
        weight: float = 1.0,
    ) -> Laminate:
        """Snapshot a SamplingPoint or its JSON output from a CLT-capable server.

        No new FE solve is performed. Older outputs without exported materials
        or laminate forces are rejected with an actionable message.
        """
        document = (
            sampling_point
            if isinstance(sampling_point, (Mapping, list))
            else (sampling_point.results)
        )
        if isinstance(document, list):
            if len(document) != 1:
                raise ValueError("Expected exactly one sampling point entry.")
            document = document[0]
        if document.get("element_type") != "shell":
            raise ValueError("Standalone CLT optimization currently supports shell laminates only.")
        try:
            definitions = document["materials"]
            materials = tuple(
                Material(m["name"], m["ext_id"], m["type"], m["properties"]) for m in definitions
            )
            material_names = {m["id"]: m["name"] for m in definitions}
            plies = tuple(
                Ply(
                    p["id"],
                    material_names[p["material"]],
                    p["angle"],
                    p["thickness"],
                    global_ply_number=p.get("global_ply_number"),
                )
                for p in document["layup"]["analysis_plies"]
            )
            if load_cases is None:
                forces = document.get("laminate_forces")
                if forces is None:
                    forces = document["results"]["laminate_forces"]
                load_cases = (LoadCase("initial", LaminateForces(**forces)),)
            return cls(
                name=name or str(document["element_label"]),
                plies=plies,
                materials=materials,
                load_cases=tuple(load_cases),
                unit_system=document["unit_system"],
                offset=document["layup"]["offset"],
                element_id=document["element_label"],
                weight=weight,
            )
        except KeyError as error:
            raise ValueError(
                f"Sampling point lacks CLT input {error}. Use a CLT-capable backend "
                "and provide explicit load_cases if resultants are not exported."
            ) from error


@dataclass(frozen=True)
class LaminateResponse:
    """CLT mass and failure results for a single point/load-case combination."""

    mass_per_unit_area: float
    inverse_reserve_factors: tuple[float, ...]
    failure_modes: tuple[str | int, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inverse_reserve_factors", tuple(self.inverse_reserve_factors))
        object.__setattr__(self, "failure_modes", tuple(self.failure_modes))
        _finite(self.mass_per_unit_area, "mass_per_unit_area", positive=True)
        if not self.inverse_reserve_factors:
            raise ValueError("Failure results must not be empty.")
        for value in self.inverse_reserve_factors:
            _finite(value, "inverse_reserve_factor")
            if value < 0:
                raise ValueError("Inverse reserve factors must not be negative.")

    @property
    def max_irf(self) -> float:
        """Maximum inverse reserve factor over all plies."""
        return max(self.inverse_reserve_factors)
