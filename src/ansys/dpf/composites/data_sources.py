"""Composite data sources."""
from dataclasses import dataclass
import os
import pathlib
from typing import Callable, Dict, Optional

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH

__all__ = (
    "CompositeDefinitionFiles",
    "ContinuousFiberCompositesFiles",
    "ShortFiberCompositesFiles",
    "CompositeDataSources",
    "get_composite_files_from_workbench_result_folder",
    "get_composites_data_sources",
)

_SOLID_COMPOSITE_DEFINITIONS_PREFIX = "ACPSolidModel"
_SHELL_COMPOSITE_DEFINITIONS_PREFIX = "ACPCompositeDefinitions"
_SETUP_FOLDER_PREFIX = "Setup"
_H5_SUFFIX = ".h5"
_MATML_FILENAME = "MatML.xml"
_RST_FILENAME = "file.rst"
_MAPPING_SUFFIX = ".mapping"


@dataclass
class CompositeDefinitionFiles:
    """Provides the container for composite definition file paths."""

    definition: _PATH
    mapping: Optional[_PATH] = None


@dataclass
class ContinuousFiberCompositesFiles:
    """Provides the container for continuous fiber composite file paths."""

    rst: _PATH
    composite: Dict[str, CompositeDefinitionFiles]
    engineering_data: _PATH
    # True if files are local and false if files
    # have already been uploaded to the server
    files_are_local: bool = True


@dataclass
class ShortFiberCompositesFiles:
    """Provides the container for short fiber composite file paths."""

    rst: _PATH
    dsdat: _PATH
    engineering_data: _PATH
    # True if files are local and false if files
    # have already been uploaded to the server
    files_are_local: bool = True


@dataclass(frozen=True)
class CompositeDataSources:
    """Provides data sources related to the composite lay-up."""

    rst: DataSources
    composite: Dict[str, DataSources]
    engineering_data: DataSources


def _get_mapping_path_file_from_definitions_path_if_exists(
    definition_path: pathlib.Path,
) -> Optional[pathlib.Path]:
    mapping_path = definition_path.parent / (definition_path.stem + _MAPPING_SUFFIX)
    return mapping_path if mapping_path.is_file() else None


def _is_rst_file(path: pathlib.Path) -> bool:
    return path.name == _RST_FILENAME and path.is_file()


def _is_matml_file(path: pathlib.Path) -> bool:
    return path.name == _MATML_FILENAME and path.is_file()


def _is_composite_definition_file(path: pathlib.Path) -> bool:
    is_composite_def = path.name.startswith(_SHELL_COMPOSITE_DEFINITIONS_PREFIX)
    return path.suffix == _H5_SUFFIX and path.is_file() and is_composite_def


def _is_solid_model_composite_definition_file(path: pathlib.Path) -> bool:
    is_h5 = path.suffix == _H5_SUFFIX
    is_file = path.is_file()
    is_def = path.name.startswith(_SOLID_COMPOSITE_DEFINITIONS_PREFIX)
    return is_h5 and is_file and is_def


def _get_single_filepath_with_predicate(
    predicate: Callable[[pathlib.Path], bool],
    folder: pathlib.Path,
    descriptive_name: str,
    accept_empty: bool = False,
) -> Optional[pathlib.Path]:
    files = [
        file_or_folder_path
        for file_or_folder_path in folder.iterdir()
        if predicate(file_or_folder_path)
    ]

    if len(files) == 0:
        if accept_empty:
            return None
        raise RuntimeError(
            f"No {descriptive_name} file found. Available files:  {os.listdir(folder)}"
        )

    if len(files) > 1:
        raise RuntimeError(f"More than one {descriptive_name} file detected {files}")

    return files[0]


def _add_composite_definitons_from_setup_folder(
    setup_folder: pathlib.Path, composite_files: ContinuousFiberCompositesFiles
) -> None:
    composite_definition = _get_single_filepath_with_predicate(
        _is_composite_definition_file, setup_folder, "composites_definition", accept_empty=True
    )

    solid_model_definition = _get_single_filepath_with_predicate(
        _is_solid_model_composite_definition_file,
        setup_folder,
        "solid_model_definition",
        accept_empty=True,
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

    -   ``rst``: The ``file.rst`` file that belongs to the cell ID of the solution
        that you want to postprocess. Multiple result files are not supported yet.
        Ensure that **Combine Distributed Result Files** is selected if the solution
        was solved in 'Distributed' mode.

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
            rst="project_root_folder/dp0/SYS/MECH/file.rst",
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

    rst_path = _get_single_filepath_with_predicate(_is_rst_file, result_folder_path, "rst")
    matml_path = _get_single_filepath_with_predicate(_is_matml_file, result_folder_path, "matml")

    assert matml_path is not None
    assert rst_path is not None

    continuous_fiber_composite_files = ContinuousFiberCompositesFiles(
        rst=rst_path.resolve(),
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
            " to False to skip this check."
        )

    return continuous_fiber_composite_files


def get_composites_data_sources(
    continuous_composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create DPF data sources from a ``ContinuousFiberCompositeFiles`` object.

    Parameters
    ----------
    continuous_composite_files
    """
    rst_data_source = DataSources(continuous_composite_files.rst)
    engineering_data_source = DataSources()
    engineering_data_source.add_file_path(
        continuous_composite_files.engineering_data, "EngineeringData"
    )
    composite_data_sources = {}
    for key, composite_files in continuous_composite_files.composite.items():
        composite_data_source = DataSources()
        composite_data_source.add_file_path(composite_files.definition, "CompositeDefinitions")

        if composite_files.mapping is not None:
            composite_data_source.add_file_path(
                composite_files.mapping, "MappingCompositeDefinitions"
            )

        composite_data_sources[key] = composite_data_source

    return CompositeDataSources(
        rst=rst_data_source,
        composite=composite_data_sources,
        engineering_data=engineering_data_source,
    )
