"""Helper to load composites plugin."""
import os
import pathlib
from typing import Optional

import ansys.dpf.core as dpf
from ansys.dpf.core.misc import get_ansys_path
from ansys.dpf.core.server_types import BaseServer

AWP_ROOT_DOCKER = "/ansys_inc/ansys/dpf/server_2023_2_pre1"


def load_composites_plugin(server: BaseServer, ansys_path: Optional[str] = None) -> None:
    r"""Load composites plugins and its dependencies.

    Parameters
    ----------
    server:
    ansys_path:
        Ansys root path, for example C:\Program Files\ANSYS Inc\v232.
        If None, it is assumed that all the plugins and their dependencies
        are found in the PATH/LD_LIBRARY_PATH. If ansys_path
        is set, the composite_operators and
        Ans.Dpf.EngineeringData plugins are loaded from their location
        in the installer.
    """
    # The automatic load of the plug can be disabled by the user and so
    # all plugins which are required for dpf composites are loaded
    libs = [
        "Ans.Dpf.Native",
        "mapdlOperatorsCore",
        "Ans.Dpf.FEMutils",
        "Ans.Dpf.EngineeringData",
        "composite_operators",
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
    }

    # March 2023 R.Roos
    # the dpf load_plugin method requires an absolute path because the dfp_composites
    # plugin is not in the search path. The logic below should support all cases
    # except a local gRPC sever on linux (local in-process server on Linux is supported)
    # DPF core team thinks about to expose ANSYS_ROOT_FOLDER so that the absolute path
    # can be easily constructed here.
    if not ansys_path:
        if server.ansys_path:
            ansys_path = server.ansys_path
        elif server.os == "posix":
            ansys_path = AWP_ROOT_DOCKER
        else:
            ansys_path = get_ansys_path()

    if not ansys_path:
        raise RuntimeError("Ansys path is not available. DPF Composites plugin cannot be loaded.")

    for name in libs:
        if name in location_in_installer:
            relative_location = location_in_installer[name][server.os]
            library = os.path.join(ansys_path, *relative_location, get_lib_from_name(name))
            if server.os == "posix":
                library = pathlib.Path(library).as_posix()
        else:
            library = get_lib_from_name(name)
        dpf.load_library(library, name, server=server)
