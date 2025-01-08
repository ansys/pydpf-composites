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

"""Indexer helper classes."""
from dataclasses import dataclass
from typing import Protocol, cast

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


class PropertyFieldIndexerProtocol(Protocol):
    """Protocol for single value property field indexer."""

    def by_id(self, entity_id: int) -> np.int64 | None:
        """
        Get index by id.

        Note: An exception is thrown if the entry has multiple values.
        """

    def by_id_as_array(self, entity_id: int) -> NDArray[np.int64] | None:
        """Get indices by id."""


def _has_data_pointer(field: PropertyField | Field) -> bool:
    if (
        field._data_pointer is not None  # pylint: disable=protected-access
        and field._data_pointer.any()  # pylint: disable=protected-access
    ):
        return True
    return False


def get_property_field_indexer(
    field: PropertyField, no_bounds_check: bool
) -> PropertyFieldIndexerProtocol:
    """Get indexer for a property field.

    Parameters
    ----------
    field: property field
    no_bounds_check: whether to get the indexer w/o bounds check. More performant but less safe.
    """
    if no_bounds_check:
        if _has_data_pointer(field):
            return PropertyFieldIndexerWithDataPointerNoBoundsCheck(field)
        return PropertyFieldIndexerNoDataPointerNoBoundsCheck(field)
    if _has_data_pointer(field):
        return PropertyFieldIndexerWithDataPointer(field)
    return PropertyFieldIndexerNoDataPointer(field)


class FieldIndexexProtocol(Protocol):
    """Protocol for single value field indexer."""

    def by_id(self, entity_id: int) -> np.double | None:
        """Get value by id."""

    def by_id_as_array(self, entity_id: int) -> NDArray[np.double] | None:
        """Get values by id."""


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
        if field.scoping.size > 0:
            index_by_id = setup_index_by_id(field.scoping)
            self._indices = index_by_id.mapping
            self._max_id = index_by_id.max_id
            self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
        else:
            self._indices = np.array([], dtype=np.int64)
            self._data = np.array([], dtype=np.int64)
            self._max_id = 0

    def by_id(self, entity_id: int) -> np.int64 | None:
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

    def by_id_as_array(self, entity_id: int) -> NDArray[np.int64] | None:
        """Get indices by id.

        Parameters
        ----------
        entity_id
        """
        value = self.by_id(entity_id)
        if value is None:
            return None
        return np.array([value], dtype=np.int64)


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

    def by_id(self, entity_id: int) -> np.int64 | None:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        if entity_id > self._max_id:
            return None
        else:
            return cast(np.int64, self._data[self._indices[entity_id]])

    def by_id_as_array(self, entity_id: int) -> NDArray[np.int64] | None:
        """Get indices by id.

        Parameters
        ----------
        entity_id
        """
        value = self.by_id(entity_id)
        if value is None:
            return None
        return np.array([value], dtype=np.int64)


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

    def by_id(self, entity_id: int) -> np.int64 | None:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        raise NotImplementedError("PropertyFieldIndexerWithDataPointer does not support by_id.")

    def by_id_as_array(self, entity_id: int) -> NDArray[np.int64] | None:
        """Get indices by ID.

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

    def by_id(self, entity_id: int) -> np.int64 | None:
        """Get index by ID.

        Parameters
        ----------
        entity_id
        """
        raise NotImplementedError(
            "PropertyFieldIndexerWithDataPointerNoBoundsCheck does not support by_id."
        )

    def by_id_as_array(self, entity_id: int) -> NDArray[np.int64] | None:
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


# DPF does not set the data pointers if a field has just
# one value per entity. Therefore, it is unknown if
# data pointer are set for some field of layered elements, for
# instance angles, thickness etc.
def get_field_indexer(field: Field) -> FieldIndexexProtocol:
    """Get field indexer based on data pointer.

    Parameters
    ----------
    field
    """
    if _has_data_pointer(field):
        return FieldIndexerWithDataPointer(field)
    return FieldIndexerNoDataPointer(field)


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

    def by_id(self, entity_id: int) -> np.double | None:
        """Get value by ID.

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

    def by_id_as_array(self, entity_id: int) -> NDArray[np.double] | None:
        """Get values by id.

        Parameters
        ----------
        entity_id
        """
        value = self.by_id(entity_id)
        if value is None:
            return None
        return np.array([value], dtype=np.double)


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

    def by_id(self, entity_id: int) -> np.double | None:
        """Get value by ID.

        Parameters
        ----------
        entity_id
        """
        values = self.by_id_as_array(entity_id)
        if values is None or len(values) == 0:
            return None
        if len(values) == 1:
            return cast(np.double, values[0])

        # There is an issue with the DPF server 2024r1_pre0 and before.
        # Values of the laminate offset field does not have length 1.
        # In this case the format of values is [offset, 0, 0., ...]
        offset = values[0]
        if all([v == 0 for v in values[1:]]):
            return cast(np.double, offset)

        raise RuntimeError(
            f"Cannot extract value for entity {entity_id}. "
            "Use the latest version of the DPF server to get the correct value. "
            f"Values: {values}"
        )

    def by_id_as_array(self, entity_id: int) -> NDArray[np.double] | None:
        """Get values by ID.

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
