# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""Composite data sources."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import os
import pathlib
from typing import cast

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH

__all__ = (
    "CompositeDefinitionFiles",
    "ContinuousFiberCompositesFiles",
    "ShortFiberCompositesFiles",
    "CompositeDataSources",
    "get_composite_files_from_workbench_result_folder",
    "composite_files_from_workbench_harmonic_analysis",
    "get_composites_data_sources",
    "get_short_fiber_composites_data_sources",
)

_SOLID_COMPOSITE_DEFINITIONS_PREFIX = "ACPSolidModel"
_SHELL_COMPOSITE_DEFINITIONS_PREFIX = "ACPCompositeDefinitions"
_SETUP_FOLDER_PREFIX = "Setup"
_H5_SUFFIX = ".h5"
_EXT_SUFFIX = "_ext"
_MATML_FILENAME = "MatML.xml"
_RST_SUFFIX = ".rst"
_RST_PREFIX = "file"
_MAPPING_SUFFIX = ".mapping"

_LAYUPFILE_INDEX_KEY = "CompositeDefinitions"
_MAPPINGFILE_INDEX_KEY = "MappingCompositeDefinitions"


@dataclass
class CompositeDefinitionFiles:
    """Provides the container for composite definition file paths."""

    definition: _PATH
    mapping: _PATH | None = None


@dataclass
class ContinuousFiberCompositesFiles:
    """Provides the container for continuous fiber composite file paths."""

    rst: list[_PATH]
    composite: dict[str, CompositeDefinitionFiles]
    engineering_data: _PATH
    solver_input_file: _PATH | None = None
    # True if files are local and false if files
    # have already been uploaded to the server
    files_are_local: bool = True

    def __init__(
        self,
        rst: list[_PATH] | _PATH,
        composite: dict[str, CompositeDefinitionFiles],
        engineering_data: _PATH,
        solver_input_file: _PATH | None = None,
        files_are_local: bool = True,
    ) -> None:
        """Initialize the ContinuousFiberCompositesFiles container.

        Parameters
        ----------
        rst :
            A single path to an RST file, or a list of paths to distributed
            RST files.
        composite :
            Dictionary of composite definition files. The key can be chosen
            freely.
        engineering_data :
            Path to the engineering data file.
        solver_input_file :
            Input file for the solver (MAPDL:``*.dat | *.cdb``, LSDyna: ``*.k``).
        files_are_local :
            True if files are on the local machine, False if they have already
            been uploaded to the DPF server..
        """
        self.rst = rst  # type: ignore
        self.composite = composite
        self.engineering_data = engineering_data
        self.solver_input_file = solver_input_file
        self.files_are_local = files_are_local

    # The constructor pretends that rst can also be just a path
    # but the property rst must be a list
    def __setattr__(self, prop, val):  # type: ignore
        """Convert values if needed."""
        if prop == "rst":
            val = self._get_rst_list(val)
        super().__setattr__(prop, val)

    @staticmethod
    def _get_rst_list(value: list[_PATH] | _PATH) -> list[_PATH]:
        if isinstance(value, (str, pathlib.Path)):
            value = [value]
        return value  # type: ignore


@dataclass
class ShortFiberCompositesFiles:
    """Provides the container for short fiber composite file paths."""

    rst: list[_PATH]
    dsdat: _PATH
    engineering_data: _PATH
    # True if files are local and false if files
    # have already been uploaded to the server
    files_are_local: bool = True

    def __init__(
        self,
        rst: list[_PATH] | _PATH,
        dsdat: _PATH,
        engineering_data: _PATH,
        files_are_local: bool = True,
    ) -> None:
        """Initialize the ShortFiberCompositesFiles container.

        Parameters
        ----------
        rst :
            A single path to an RST file, or a list of paths to distributed
            RST files.
        dsdat :
            Path to the solver input file (``ds.dat``).
        engineering_data :
            Path to the engineering data file.
        files_are_local :
            True if files are on the local machine, False if they have already
            been uploaded to the DPF server..
        """
        self.rst = rst  # type: ignore
        self.dsdat = dsdat
        self.engineering_data = engineering_data
        self.files_are_local = files_are_local

    # The constructor pretends that rst can also be just a path
    # but the property rst must be a list.
    def __setattr__(self, prop, val):  # type: ignore
        """Convert values if needed."""
        if prop == "rst":
            val = self._get_rst_list(val)
        super().__setattr__(prop, val)

    @staticmethod
    def _get_rst_list(value: list[_PATH] | _PATH) -> list[_PATH]:
        if isinstance(value, (str, pathlib.Path)):
            value = [value]
        return value  # type: ignore


@dataclass(frozen=True)
class CompositeDataSources:
    """Provides data sources related to the composite lay-up.

    Parameters
    ----------
    rst:
        Result file. Currently only RST (MAPDL) is supported.

    material_support:
        NOTE: The ``material_support`` parameter is explicitly listed because it is currently not
        supported (by the DPF Core) to use a distributed RST file as source for the
        material support. Instead, we create a separate DataSources object for the
        material support from the first RST file. This is a workaround until the
        support for distributed RST is added.
    engineering_data:
        File with the material properties.
    solver_input_file:
        Input file for the solver (MAPDL:``*.dat | *.cdb``, LSDyna: ``*.k``).

    old_composite_sources :
        Member used to support assemblies in combination with the old
        DPF server (<7.0). It should be removed once the support of this
        server version is dropped.

    """

    rst: DataSources
    material_support: DataSources
    composite: DataSources | None
    engineering_data: DataSources
    solver_input_file: DataSources | None

    old_composite_sources: dict[str, DataSources]


def _get_mapping_path_file_from_definitions_path_if_exists(
    definition_path: pathlib.Path,
) -> pathlib.Path | None:
    mapping_path = definition_path.parent / (definition_path.stem + _MAPPING_SUFFIX)
    return mapping_path if mapping_path.is_file() else None


def _is_rst_file(path: pathlib.Path) -> bool:
    return path.name.startswith(_RST_PREFIX) and path.suffix == _RST_SUFFIX and path.is_file()


def _is_matml_file(path: pathlib.Path) -> bool:
    return path.name == _MATML_FILENAME and path.is_file()


def _has_ext_suffix(path: pathlib.Path) -> bool:
    """Check if the stem (filename without extension) ends with ``_ext``.

    Example: CompositeDefinitions.1_ext.h5
    """
    return path.stem.endswith("_ext")


def _is_composite_definition_file(path: pathlib.Path) -> bool:
    is_composite_def = path.name.startswith(_SHELL_COMPOSITE_DEFINITIONS_PREFIX)
    no_ext_suffix = not _has_ext_suffix(path)
    return path.suffix == _H5_SUFFIX and path.is_file() and is_composite_def and no_ext_suffix


def _is_solid_model_composite_definition_file(path: pathlib.Path) -> bool:
    is_h5 = path.suffix == _H5_SUFFIX
    has_ext_suffix = _has_ext_suffix(path)
    is_file = path.is_file()
    is_def = path.name.startswith(_SOLID_COMPOSITE_DEFINITIONS_PREFIX)
    return is_h5 and is_file and is_def and not has_ext_suffix


def _get_file_paths_with_predicate(
    predicate: Callable[[pathlib.Path], bool],
    folder: pathlib.Path,
) -> Sequence[pathlib.Path]:
    files = [
        file_or_folder_path
        for file_or_folder_path in folder.iterdir()
        if predicate(file_or_folder_path)
    ]
    return files


def _get_single_file_path_with_predicate(
    predicate: Callable[[pathlib.Path], bool],
    folder: pathlib.Path,
    descriptive_name: str,
) -> pathlib.Path:
    files = _get_file_paths_with_predicate(predicate, folder)
    if len(files) != 1:
        raise RuntimeError(
            f"Expected exactly one {descriptive_name} file. Found {files}."
            f" Available files in folder: {os.listdir(folder)}"
        )

    return files[0]


def _get_single_optional_file_path_with_predicate(
    predicate: Callable[[pathlib.Path], bool],
    folder: pathlib.Path,
    descriptive_name: str,
) -> pathlib.Path | None:
    files = _get_file_paths_with_predicate(predicate, folder)
    if len(files) > 1:
        raise RuntimeError(f"Expected no more than one {descriptive_name} file. Found {files}.")
    if len(files) == 0:
        return None
    return files[0]


def _add_composite_definitons_from_setup_folder(
    setup_folder: pathlib.Path, composite_files: ContinuousFiberCompositesFiles
) -> None:
    composite_definition = _get_single_optional_file_path_with_predicate(
        _is_composite_definition_file,
        setup_folder,
        "composites_definition",
    )

    solid_model_definition = _get_single_optional_file_path_with_predicate(
        _is_solid_model_composite_definition_file, setup_folder, "solid_model_definition"
    )

    def get_composite_definitions_files(
        composite_definition_path: pathlib.Path,
    ) -> CompositeDefinitionFiles:
        mapping_path = _get_mapping_path_file_from_definitions_path_if_exists(
            composite_definition_path
        )
        return CompositeDefinitionFiles(
            definition=composite_definition_path.resolve(),
            mapping=mapping_path.resolve() if mapping_path is not None else None,
        )

    if composite_definition is not None:
        definition_files = get_composite_definitions_files(composite_definition)
        key = os.path.basename(setup_folder) + "_shell"
        if key in composite_files.composite:
            raise RuntimeError(f"Definition with key already exists {key}")
        composite_files.composite[key] = definition_files

    if solid_model_definition is not None:
        definition_files = get_composite_definitions_files(solid_model_definition)
        key = os.path.basename(setup_folder) + "_solid"

        if key in composite_files.composite:
            raise RuntimeError(f"Definition with key already exists {key}")
        composite_files.composite[key] = definition_files


def composite_files_from_workbench_harmonic_analysis(
    result_folder_modal: _PATH, result_folder_harmonic: _PATH
) -> ContinuousFiberCompositesFiles:
    """Get a ``ContinuousFiberCompositesFiles`` object for a harmonic analysis.

    Parameters
    ----------
    result_folder_modal : str
       Result folder of the Modal solution.
       In the Modal system, right-click the **solution** item in the Ansys Mechanical tree
       and select **Open Solver Files Directory** to obtain the result folder.
    result_folder_harmonic : str
       Result folder of the Harmonic Response solution.
       In the Harmonic Response system,
       right-click the **solution** item in the Ansys Mechanical tree
       and select **Open Solver Files Directory** to obtain the result folder.

    """
    result_folder_path_harmonic = pathlib.Path(result_folder_harmonic)
    result_folder_path_modal = pathlib.Path(result_folder_modal)

    setup_folders_modal = [
        folder_path
        for folder_path in result_folder_path_modal.iterdir()
        if folder_path.is_dir() and folder_path.name.startswith(_SETUP_FOLDER_PREFIX)
    ]

    rst_paths = _get_file_paths_with_predicate(
        _is_rst_file,
        result_folder_path_harmonic,
    )

    if len(rst_paths) == 0:
        raise RuntimeError(
            f"Expected at least one rst file. Found {rst_paths}."
            f" Available files in folder: {os.listdir(result_folder_path_harmonic)}"
        )

    matml_path = _get_single_file_path_with_predicate(
        _is_matml_file,
        result_folder_path_harmonic,
        "matml",
    )

    assert matml_path is not None
    assert rst_paths is not None

    continuous_fiber_composite_files = ContinuousFiberCompositesFiles(
        rst=[rst_path.resolve() for rst_path in rst_paths],
        composite={},
        engineering_data=matml_path.resolve(),
    )

    for setup_folder in setup_folders_modal:
        _add_composite_definitons_from_setup_folder(setup_folder, continuous_fiber_composite_files)

    return continuous_fiber_composite_files


def get_composite_files_from_workbench_result_folder(
    result_folder: _PATH, ensure_composite_definitions_found: bool = True
) -> ContinuousFiberCompositesFiles:
    r"""Get a ``ContinuousFiberCompositesFiles`` object from a result folder.

    This function assumes a typical Workbench folder structure for a composite
    simulation. If this method is not able to build the ``ContinuousFiberCompositesFiles``
    object, you can follow these steps:

    In the main Workbench window, activate the files panel by selecting
    **View > Files**. This shows the location of all files used in the
    workbench project. You can determine the different attributes of the
    ``ContinuousFiberCompositesFiles`` object:

    -   ``rst``: A list of files containing either the single ``file.rst``
        file that belongs to the cell ID of the solution, or the distributed
        ``file0.rst`` to ``fileN.rst`` files.

    -   ``engineering_data``: The ``MatML.xml`` file in the same folder as the RST file.

    -   ``composite``: There can be multiple composite definitions,
        one definition for each ACP system if shell data is transferred
        and one definition for each solid model if solid data is transferred.
        All the ``ACPCompositeDefinitions.h5`` and ``ACPSolidModel*.h5``
        files that are used in the solution must be added to the
        ``ContinuousFiberCompositesFiles.composite`` dictionary.
        The key can be chosen freely. Next to the ``ACPCompositeDefinitions.h5``
        and ``ACPSolidModel\*.h5`` files, corresponding ``ACPCompositeDefinitions.mapping``
        and ``ACPSolidModel*.mapping`` files can be found (optional).
        If they exist, they must be added as well.

    The following example shows how a
    :class:`.ContinuousFiberCompositesFiles` object can be built.
    The project in this example has two **ACP Pre** systems, one that exports
    shell information and one that exports solid information.

    The files are located in these locations:

    Result file:

    - ``project_root_folder/dp0/SYS/MECH/file.rst``

    Engineering data file:

    - ``project_root_folder/dp0/SYS/MECH/MatML.xml``

    Composite definition and mapping files for the solid model:

    - ``project_root_folder/dp0/ACP-Pre-1/ACPSolidModel_SM.h5``
    - ``project_root_folder/dp0/ACP-Pre-1/ACPSolidModel_SM.mapping``

    Composite definition and mapping files for the shell model:

    - ``project_root_folder/dp0/ACP-Pre-2/ACPCompositeDefinitions.h5``
    - ``project_root_folder/dp0/ACP-Pre-2/ACPCompositeDefinitions.mapping``

    The code creates the corresponding ``ContinuousFiberCompositesFiles`` object::

        ContinuousFiberCompositesFiles(
            rst=["project_root_folder/dp0/SYS/MECH/file.rst"],
            composite={
               "solid": CompositeDefinitionFiles(
                    definition="project_root_folder/dp0/ACP-Pre-1/ACPSolidModel_SM.h5",
                    mapping="project_root_folder/dp0/ACP-Pre-1/ACPSolidModel_SM.mapping"
                ),
               "shell": CompositeDefinitionFiles(
                    definition="project_root_folder/dp0/ACP-Pre-2/ACPCompositeDefinitions.h5",
                    mapping="project_root_folder/dp0/ACP-Pre-2/ACPCompositeDefinitions.mapping"
                )
            },
            engineering_data="project_root_folder/dp0/SYS/MECH/MatML.xml"
        )

    Parameters
    ----------
    result_folder :
       Result folder of the solution. Right-click the **solution** item in the Ansys Mechanical tree
       and select **Open Solver Files Directory** to obtain the result folder.
    ensure_composite_definitions_found :
        Whether to check if at least one composite definition (shell or solid) has been found.
    """
    result_folder_path = pathlib.Path(result_folder)

    setup_folders = [
        folder_path
        for folder_path in result_folder_path.iterdir()
        if folder_path.is_dir() and folder_path.name.startswith(_SETUP_FOLDER_PREFIX)
    ]

    rst_paths = _get_file_paths_with_predicate(
        _is_rst_file,
        result_folder_path,
    )

    if len(rst_paths) == 0:
        raise RuntimeError(
            f"Expected at least one rst file. Found {rst_paths}."
            f" Available files in folder: {os.listdir(result_folder_path)}"
        )

    matml_path = _get_single_file_path_with_predicate(
        _is_matml_file,
        result_folder_path,
        "matml",
    )

    assert matml_path is not None
    assert rst_paths is not None

    continuous_fiber_composite_files = ContinuousFiberCompositesFiles(
        rst=[rst_path.resolve() for rst_path in rst_paths],
        composite={},
        engineering_data=matml_path.resolve(),
    )

    for setup_folder in setup_folders:
        _add_composite_definitons_from_setup_folder(setup_folder, continuous_fiber_composite_files)

    if (
        ensure_composite_definitions_found
        and len(list(continuous_fiber_composite_files.composite.keys())) == 0
    ):
        raise RuntimeError(
            "No composite definitions found. Set "
            "ensure_composite_definitions_found argument"
            " to False to skip this check. Note: Use the function"
            " composite_files_from_workbench_harmonic_analysis if this is a harmonic analysis."
        )

    return continuous_fiber_composite_files


def _get_data_sources_from_rst_files(
    rst_files: list[_PATH],
) -> DataSources:
    """Get a DPF data sources object from a list of RST files.

    If a single RST file is provided, it is added via 'set_result_file_path'.
    Otherwise, the RST files are added via 'set_domain_result_file_path'.
    """
    data_sources = DataSources()
    if len(rst_files) == 1:
        data_sources.set_result_file_path(rst_files[0])
    else:
        for idx, rst_file in enumerate(rst_files):
            data_sources.set_domain_result_file_path(rst_file, idx)
    return data_sources


def get_composites_data_sources(
    continuous_composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create DPF data sources from a ``ContinuousFiberCompositeFiles`` object.

    Parameters
    ----------
    continuous_composite_files
    """
    if not continuous_composite_files.rst:
        raise RuntimeError("No rst files found.")
    else:
        rst_data_source = _get_data_sources_from_rst_files(continuous_composite_files.rst)

        # NOTE: The 'material_support' is explicitly listed since it is currently not
        # supported (by the DPF Core) to use a distributed RST file as source for the
        # material support. Instead, we create a separate DataSources object for the
        # material support from the first RST file. This is a workaround until the
        # support for distributed RST is added.
        if len(continuous_composite_files.rst) == 1:
            material_support_data_source = rst_data_source
        else:
            material_support_data_source = _get_data_sources_from_rst_files(
                [continuous_composite_files.rst[0]]
            )

    engineering_data_source = DataSources()
    engineering_data_source.add_file_path(
        continuous_composite_files.engineering_data, "EngineeringData"
    )

    composite_data_source = DataSources()
    set_part_key = len(continuous_composite_files.composite) > 1
    old_composite_data_sources = {}

    for key, composite_files in continuous_composite_files.composite.items():
        if set_part_key:
            composite_data_source.add_file_path_for_specified_result(
                composite_files.definition, _LAYUPFILE_INDEX_KEY, key
            )
        else:
            composite_data_source.add_file_path(composite_files.definition, _LAYUPFILE_INDEX_KEY)

        if composite_files.mapping is not None:
            if set_part_key:
                composite_data_source.add_file_path_for_specified_result(
                    composite_files.mapping, _MAPPINGFILE_INDEX_KEY, key
                )
            else:
                composite_data_source.add_file_path(composite_files.mapping, _MAPPINGFILE_INDEX_KEY)

        ##### This block is needed to support DPF Server older than 7.0 (2023 R2 or before)
        old_datasource = DataSources()
        old_datasource.add_file_path(composite_files.definition, _LAYUPFILE_INDEX_KEY)
        if composite_files.mapping is not None:
            old_datasource.add_file_path(composite_files.mapping, _MAPPINGFILE_INDEX_KEY)
        ##### End of block

        old_composite_data_sources[key] = old_datasource

    # Reset composite data source if no composite files are provided because a
    # data source cannot be empty
    if len(continuous_composite_files.composite) == 0:
        composite_data_source = None

    solver_input_file_data_sources = None
    if continuous_composite_files.solver_input_file is not None:
        solver_input_file_data_sources = DataSources()
        solver_input_file_data_sources.add_file_path(
            continuous_composite_files.solver_input_file, "LsDynaInputFile"
        )

    return CompositeDataSources(
        rst=rst_data_source,
        material_support=material_support_data_source,
        composite=composite_data_source,
        engineering_data=engineering_data_source,
        solver_input_file=solver_input_file_data_sources,
        old_composite_sources=old_composite_data_sources,
    )


def _data_sources_num_result_keys(data_sources: DataSources) -> int:
    # pylint: disable=protected-access
    return cast(
        int,
        data_sources._api.data_sources_get_num_result_keys(data_sources),
    )


def _data_sources_result_key(data_sources: DataSources, index: int) -> str:
    # pylint: disable=protected-access
    return cast(
        str,
        data_sources._api.data_sources_get_result_key_by_index(data_sources, index),
    )


def get_short_fiber_composites_data_sources(
    short_fiber_composites_files: ShortFiberCompositesFiles,
) -> DataSources:
    """
    Create DPF data sources from a ``ShortFiberCompositeFiles`` object.

    Parameters
    ----------
    short_fiber_composite_files :
        Container for short fiber composite file paths.
    """
    data_sources = _get_data_sources_from_rst_files(short_fiber_composites_files.rst)
    data_sources.add_file_path(short_fiber_composites_files.dsdat, "dat")
    data_sources.add_file_path(short_fiber_composites_files.engineering_data, "EngineeringData")
    return data_sources
