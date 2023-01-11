"""Helper to load composites plugin."""
import os
from typing import Optional

import ansys.dpf.core as dpf


def load_composites_plugin(server: dpf.server, ansys_path: Optional[str] = None) -> None:
    """Load composites plugins and its dependencies."""
    libs = [
        "Ans.Dpf.Native",
        "mapdlOperatorsCore",
        "Ans.Dpf.FEMutils",
        "composite_operators",
        "Ans.Dpf.EngineeringData",
    ]

    def get_lib_from_name(name: str) -> str:
        if server.os == "posix":
            return f"lib{name}.so"
        elif server.os == "nt":
            return f"{name}.dll"
        else:
            raise RuntimeError(f"Invalid server os: {server.os}")

    location_in_installer = {
        "composite_operators": {
            "nt": ["dpf", "plugins", "dpf_composites"],
            "posix": ["dpf", "plugins", "dpf_composites"],
        },
        "Ans.Dpf.EngineeringData": {
            "nt": ["dpf", "bin", "winx64"],
            "posix": ["dpf", "dll", "linx64"],
        },
    }

    for name in libs:
        if ansys_path is not None and name in location_in_installer:
            relative_installer_location = location_in_installer[name][server.os]
            absolute_installer_location = os.path.join(ansys_path, *relative_installer_location)
            library = os.path.join(absolute_installer_location, get_lib_from_name(name))
        else:
            library = get_lib_from_name(name)
        dpf.load_library(library, name, server=server)
