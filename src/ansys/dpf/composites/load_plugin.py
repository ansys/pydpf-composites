"""Helper to load composites plugin."""

import sys
from typing import Optional

import ansys.dpf.core as dpf


def load_composites_plugin(platform: Optional[str] = None, server: Optional[str] = None) -> None:
    """Load composites plugins and its dependencies."""
    if platform is None:
        platform = sys.platform

    libs = [
        "composite_operators",
        "Ans.Dpf.EngineeringData",
        "Ans.Dpf.Native",
        "mapdlOperatorsCore",
        "Ans.Dpf.FEMutils",
    ]

    for name in libs:
        if platform == "linux":
            filename = f"lib{name}.so"
        else:
            filename = f"{name}.dll"
        dpf.load_library(filename, name, server=server)
