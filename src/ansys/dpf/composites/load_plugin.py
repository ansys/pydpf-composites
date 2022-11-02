"""Helper to load composites plugin."""

import sys
from typing import Optional

import ansys.dpf.core as dpf
from ansys.dpf.gate.errors import DPFServerException


def load_composites_plugin(platform: Optional[str] = None, server: Optional[str] = None) -> None:
    """Load composites plugins and its dependencies."""
    if platform is None:
        # If the platform is not specified, we try loading the plugins in
        # both ways. Because the server may run in a container or remotely,
        # we cannot guess the server platform from the client side.
        #
        # This is a bit of a hack; it would be nicer if we could simply specify
        # the library name, and the server would expand it to the platform-specific
        # full name.
        try:
            load_composites_plugin(platform="win32", server=server)
        except DPFServerException:
            load_composites_plugin(platform="linux", server=server)
        return

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
