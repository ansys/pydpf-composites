"""Helpers for defining type annotations."""
import os
from typing import Union

__all__ = ["PATH"]

PATH = Union[str, os.PathLike]
