"""Composite Data Sources."""
from dataclasses import dataclass, field
from typing import Sequence

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH


@dataclass
class ContinuousFiberCompositesFiles:
    """Container for continuous fiber file paths."""

    rst: _PATH
    composite_definitions: _PATH
    engineering_data: _PATH
    mapping_files: Sequence[_PATH] = field(default_factory=lambda: [])


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
    composites_files: DataSources
    engineering_data: DataSources


def get_composites_data_sources(
    composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create dpf data sources from a ContinuousFiberCompositeFiles object.

    Parameters
    ----------
    composite_files
    """
    rst_data_source = DataSources(composite_files.rst)
    engineering_data_source = DataSources()
    engineering_data_source.add_file_path(composite_files.engineering_data, "EngineeringData")
    composite_data_source = DataSources()
    composite_data_source.add_file_path(
        composite_files.composite_definitions, "CompositeDefinitions"
    )

    for mapping_file in composite_files.mapping_files:
        composite_data_source.add_file_path(
            mapping_file,
            "MappingCompositeDefinitions",
        )

    return CompositeDataSources(
        rst=rst_data_source,
        composites_files=composite_data_source,
        engineering_data=engineering_data_source,
    )
