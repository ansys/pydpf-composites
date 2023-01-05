"""Composite Data Sources."""
from dataclasses import dataclass
from typing import Dict, Optional

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH


@dataclass
class CompositeDefinitionFiles:
    """Container for composite files (per scope)."""

    definition: _PATH
    mapping: Optional[_PATH] = None


@dataclass
class ContinuousFiberCompositesFiles:
    """Container for continuous fiber file paths."""

    rst: _PATH
    composite: Dict[str, CompositeDefinitionFiles]
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
    composite: Dict[str, DataSources]
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
