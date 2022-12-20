"""Composite Data Sources."""
from dataclasses import dataclass
from typing import Optional

from ansys.dpf.core import DataSources

from ._typing_helper import PATH as _PATH


@dataclass
class ContinuousFiberCompositesFiles:
    """Container for continuous fiber file paths."""

    rst: _PATH = ""
    composite_definitions: _PATH = ""
    engineering_data: _PATH = ""


@dataclass
class ShortFiberCompositesFiles:
    """Container for short fiber file paths."""

    rst: Optional[_PATH] = ""
    dsdat: Optional[_PATH] = ""
    engineering_data: Optional[_PATH] = ""


@dataclass(frozen=True)
class CompositeDataSources:
    """Data Sources related to the composite Layup."""

    rst: DataSources
    composites_files: DataSources


def get_composites_data_sources(
    composite_files: ContinuousFiberCompositesFiles,
) -> CompositeDataSources:
    """Create dpf data sources from a ContinuousFibercompositeFiles object.

    Parameters
    ----------
    composite_files
    """
    rst_data_source = DataSources(composite_files.rst)
    composite_data_source = DataSources()
    composite_data_source.add_file_path(composite_files.engineering_data, "EngineeringData")
    composite_data_source.add_file_path(
        composite_files.composite_definitions, "CompositeDefinitions"
    )

    return CompositeDataSources(rst=rst_data_source, composites_files=composite_data_source)
