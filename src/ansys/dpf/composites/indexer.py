"""Indexer helper classes."""
import sys
from typing import Optional, cast

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from ansys.dpf.core import Field, PropertyField, Scoping
import numpy as np
from numpy.typing import NDArray


def _setup_index_by_id(scoping: Scoping) -> NDArray[np.int64]:
    # Setup array that can be indexed by id to get the index.
    # For ids which are not present in the scoping the array has a value of -1
    indices: NDArray[np.int64] = np.full(max(scoping.ids) + 1, -1, dtype=np.int64)
    indices[scoping.ids] = np.arange(len(scoping.ids))
    return indices


class _PropertyFieldIndexerSingleValue(Protocol):
    def by_id(self, entity_id: int) -> Optional[np.int64]:
        pass


class _PropertyFieldIndexerArrayValue(Protocol):
    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        pass


# General comment for all Indexer:
# The .data call accesses the actual data. This sends the data over grpc which takes some time
# It looks like it returns a DpfArray for non-local fields and an numpy array for local fields.
# Without converting the DpfArray to a numpy array,
# performance during the lookup is about 50% slower.
# It is not clear why. To be checked with dpf team. If this is a local field there is no
# performance difference because the local field implementation already returns a numpy
# array


class _PropertyFieldIndexerNoDataPointer:
    def __init__(self, field: PropertyField):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        if entity_id > self.max_id:
            return None
        return cast(np.int64, self.data[self.indices[entity_id]])


class _FieldIndexerNoDataPointer:
    def __init__(self, field: Field):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.double] = np.array(field.data, dtype=np.double)
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Optional[np.double]:
        if entity_id > self.max_id:
            return None
        return cast(np.double, self.data[self.indices[entity_id]])


class _PropertyFieldIndexerNoDataPointerNoBoundsCheck:
    def __init__(self, field: PropertyField):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        return cast(np.int64, self.data[self.indices[entity_id]])


class _PropertyFieldIndexerWithDataPointer:
    def __init__(self, field: PropertyField):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
        self.n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self.data) * self.n_components
        )
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        if entity_id > self.max_id:
            return None

        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.int64],
            self.data[
                self._data_pointer[idx]
                // self.n_components : self._data_pointer[idx + 1]
                // self.n_components
            ],
        )


class _FieldIndexerWithDataPointer:
    def __init__(self, field: Field):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.double] = np.array(field.data, dtype=np.double)
        self.n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self.data) * self.n_components
        )
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Optional[NDArray[np.double]]:
        if entity_id > self.max_id:
            return None

        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.double],
            self.data[
                self._data_pointer[idx]
                // self.n_components : self._data_pointer[idx + 1]
                // self.n_components
            ],
        )


class _PropertyFieldIndexerWithDataPointerNoBoundsCheck:
    def __init__(self, field: PropertyField):
        self.indices = _setup_index_by_id(field.scoping)
        self.data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

        self.n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self.data) * self.n_components
        )
        self.max_id = len(self.indices) - 1

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
        idx = self.indices[entity_id]
        if idx < 0:
            return None
        return cast(
            NDArray[np.int64],
            self.data[
                self._data_pointer[idx]
                // self.n_components : self._data_pointer[idx + 1]
                // self.n_components
            ],
        )
