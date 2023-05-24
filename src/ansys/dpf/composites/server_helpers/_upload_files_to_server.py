from typing import cast

import ansys.dpf.core as dpf
from ansys.dpf.core.server_types import BaseServer

from .._typing_helper import PATH as _PATH
from ..data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
    ShortFiberCompositesFiles,
)


def upload_short_fiber_composite_files_to_server(
    data_files: ShortFiberCompositesFiles, server: BaseServer
) -> ShortFiberCompositesFiles:
    """Upload short fiber composites files to server.

    Parameters
    ----------
    data_files
    server
    """
    # If files are not local, it means they have already been
    # uploaded to the server
    if server.local_server or not data_files.files_are_local:
        return data_files

    def upload(filename: _PATH) -> str:
        return cast(str, dpf.upload_file_in_tmp_folder(filename, server=server))

    return ShortFiberCompositesFiles(
        rst=upload(data_files.engineering_data),
        dsdat=upload(data_files.dsdat),
        engineering_data=upload(data_files.engineering_data),
        files_are_local=False,
    )


def upload_continuous_fiber_composite_files_to_server(
    data_files: ContinuousFiberCompositesFiles, server: BaseServer
) -> ContinuousFiberCompositesFiles:
    """Upload continuous fiber composites files to server.

    Note: If server.local_server == True the data_files are returned unmodified.

    Parameters
    ----------
    data_files
    server
    """
    # If files are not local, it means they have already been
    # uploaded to the server
    if server.local_server or not data_files.files_are_local:
        return data_files

    def upload(filename: _PATH) -> _PATH:
        return cast(str, dpf.upload_file_in_tmp_folder(filename, server=server))

    all_composite_files = {}
    for key, composite_files_by_scope in data_files.composite.items():
        composite_definition_files = CompositeDefinitionFiles(
            definition=upload(composite_files_by_scope.definition),
        )

        if composite_files_by_scope.mapping is not None:
            composite_definition_files.mapping = upload(composite_files_by_scope.mapping)

        all_composite_files[key] = composite_definition_files

    return ContinuousFiberCompositesFiles(
        rst=upload(data_files.rst),
        engineering_data=upload(data_files.engineering_data),
        composite=all_composite_files,
        files_are_local=False,
    )
