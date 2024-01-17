# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""Indexer helper classes."""
from dataclasses import dataclass
from typing import Optional, Protocol, cast

from ansys.dpf.core import Field, PropertyField, Scoping
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class IndexToId:
    """Mapping maps id to index."""

    mapping: NDArray[np.int64]
    max_id: int


def setup_index_by_id(scoping: Scoping) -> IndexToId:
    """Create array that can be indexed by id to get the index.

    For ids which are not present in the scoping the array has a value of -1

    Parameters
    ----------
    scoping:
        DPF scoping
    """
    indices: NDArray[np.int64] = np.full(max(scoping.ids) + 1, -1, dtype=np.int64)
    indices[scoping.ids] = np.arange(len(scoping.ids))
    return IndexToId(mapping=indices, max_id=len(indices) - 1)


class PropertyFieldIndexerSingleValue(Protocol):
    """Protocol for single value property field indexer."""

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        """Get index by id."""


class PropertyFieldIndexerArrayValue(Protocol):
    """Protocol for array valued property field indexer."""

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        """Get index by id."""


# General comment for all Indexer:
# The .data call accesses the actual data. This sends the data over grpc which takes some time
# It looks like it returns a DpfArray for non-local fields and an numpy array for local fields.
# Without converting the DpfArray to a numpy array,
# performance during the lookup is about 50% slower.
# It is not clear why. To be checked with dpf team. If this is a local field there is no
# performance difference because the local field implementation already returns a numpy
# array


class PropertyFieldIndexerNoDataPointer:
    """Indexer for a property field with no data pointer."""

    def __init__(self, field: PropertyField):
        """Create indexer and get data."""
        index_by_id = setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._max_id = index_by_id.max_id
        self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        """Get index by id.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None

        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(np.int64, self._data[idx])


class FieldIndexerNoDataPointer:
    """Indexer for a dpf field with no data pointer."""

    def __init__(self, field: Field):
        """Create indexer and get data."""
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping
            self._max_id = index_by_id.max_id
            self._data: NDArray[np.double] = np.array(field.data, dtype=np.double)
        else:
            self._indices = np.array([], dtype=np.int64)
            self._max_id = 0
            self._data = np.array([], dtype=np.double)

    def by_id(self, entity_id: int) -> Optional[np.double]:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None
        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(np.double, self._data[idx])


class PropertyFieldIndexerNoDataPointerNoBoundsCheck:
    """Indexer for a property field with no data pointer and no bounds checks."""

    def __init__(self, field: PropertyField):
        """Create indexer and get data."""
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping
            self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
            self._max_id = index_by_id.max_id
        else:
            self._indices = np.array([], dtype=np.int64)
            self._data = np.array([], dtype=np.int64)
            self._max_id = 0

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None
        else:
            return cast(np.int64, self._data[self._indices[entity_id]])


class PropertyFieldIndexerWithDataPointer:
    """Indexer for a property field with data pointer."""

    def __init__(self, field: PropertyField):
        """Create indexer and get data."""
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping
            self._max_id = index_by_id.max_id

            self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
            self._n_components = field.component_count

            self._data_pointer: NDArray[np.int64] = np.append(
                field._data_pointer, len(self._data) * self._n_components
            )
        else:
            self._max_id = 0
            self._indices = np.array([], dtype=np.int64)
            self._data = np.array([], dtype=np.int64)
            self._n_components = 0
            self._data_pointer = np.array([], dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None

        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.int64],
            self._data[
                self._data_pointer[idx]
                // self._n_components : self._data_pointer[idx + 1]
                // self._n_components
            ],
        )


class FieldIndexerWithDataPointer:
    """Indexer for a dpf field with data pointer."""

    def __init__(self, field: Field):
        """Create indexer and get data."""
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping
            self._max_id = index_by_id.max_id

            self._data: NDArray[np.double] = np.array(field.data, dtype=np.double)
            self._n_components = field.component_count

            self._data_pointer: NDArray[np.int64] = np.append(
                field._data_pointer, len(self._data) * self._n_components
            )
        else:
            self._max_id = 0
            self._indices = np.array([], dtype=np.int64)
            self._data = np.array([], dtype=np.double)
            self._n_components = 0
            self._data_pointer = np.array([], dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[NDArray[np.double]]:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None

        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.double],
            self._data[
                self._data_pointer[idx]
                // self._n_components : self._data_pointer[idx + 1]
                // self._n_components
            ],
        )


class PropertyFieldIndexerWithDataPointerNoBoundsCheck:
    """Indexer for a property field with data pointer and no bounds checks."""

    def __init__(self, field: PropertyField):
        """Create indexer and get data."""
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping

            self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
            self._n_components = field.component_count

            self._data_pointer: NDArray[np.int64] = np.append(
                field._data_pointer, len(self._data) * self._n_components
            )
        else:
            self._indices = np.array([], dtype=np.int64)
            self._data = np.array([], dtype=np.int64)
            self._n_components = 0
            self._data_pointer = np.array([], dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.int64],
            self._data[
                self._data_pointer[idx]
                // self._n_components : self._data_pointer[idx + 1]
                // self._n_components
            ],
        )
