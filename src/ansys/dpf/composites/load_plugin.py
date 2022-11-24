"""Helper to load composites plugin."""

import ansys.dpf.core as dpf


def load_composites_plugin(server: dpf.server) -> None:
    """Load composites plugins and its dependencies."""
    libs = [
        "composite_operators",
        "Ans.Dpf.EngineeringData",
        "Ans.Dpf.Native",
        "mapdlOperatorsCore",
        "Ans.Dpf.FEMutils",
    ]

    for name in libs:
        if server.os == "posix":
            filename = f"lib{name}.so"
        elif server.os == "nt":
            filename = f"{name}.dll"
        else:
            raise RuntimeError(f"Invalid server os: {server.os}")

        dpf.load_library(filename, name, server=server)
