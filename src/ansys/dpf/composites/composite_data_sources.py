"""Composite Data Sources."""
from dataclasses import dataclass, field
from typing import Dict, Sequence

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH


@dataclass
class CompositeFiles:
    """Container for composite files (per scope)."""

    composite_definitions: _PATH
    mapping_files: Sequence[_PATH] = field(default_factory=lambda: [])


@dataclass
class ContinuousFiberCompositesFiles:
    """Container for continuous fiber file paths."""

    rst: _PATH
    composite_files: Dict[str, CompositeFiles]
    engineering_data: _PATH


@dataclass
class ShortFiberCompositesFiles:
    """Container for short fiber file paths."""

    rst: _PATH
    dsdat: _PATH
    engineering_data: _PATH


@dataclass(frozen=True)
class CompositeDataSources:
    """Data Sources related to the composite Layup."""

    rst: DataSources
    composites_files: Dict[str, DataSources]
    engineering_data: DataSources


def get_composites_data_sources(
    continuous_composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create dpf data sources from a ContinuousFiberCompositeFiles object.

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
    for key, composite_files in continuous_composite_files.composite_files.items():
        composite_data_source = DataSources()
        composite_data_source.add_file_path(
            composite_files.composite_definitions, "CompositeDefinitions"
        )
        for mapping_file in composite_files.mapping_files:
            composite_data_source.add_file_path(
                mapping_file,
                "MappingCompositeDefinitions",
            )

        composite_data_sources[key] = composite_data_source

    return CompositeDataSources(
        rst=rst_data_source,
        composites_files=composite_data_sources,
        engineering_data=engineering_data_source,
    )
