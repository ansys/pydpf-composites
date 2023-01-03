"""Indexer helper classes."""
from dataclasses import dataclass
import sys
from typing import Optional, cast

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from ansys.dpf.core import Field, PropertyField, Scoping
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class _IndexToId:
    mapping: NDArray[np.int64]
    max_id: int


def _setup_index_by_id(scoping: Scoping) -> _IndexToId:
    # Setup array that can be indexed by id to get the index.
    # For ids which are not present in the scoping the array has a value of -1
    indices: NDArray[np.int64] = np.full(max(scoping.ids) + 1, -1, dtype=np.int64)
    indices[scoping.ids] = np.arange(len(scoping.ids))
    return _IndexToId(mapping=indices, max_id=len(indices) - 1)


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
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._max_id = index_by_id.max_id
        self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        if entity_id > self._max_id:
            return None

        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(np.int64, self._data[idx])


class _FieldIndexerNoDataPointer:
    def __init__(self, field: Field):
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._max_id = index_by_id.max_id
        self._data: NDArray[np.double] = np.array(field.data, dtype=np.double)

    def by_id(self, entity_id: int) -> Optional[np.double]:
        if entity_id > self._max_id:
            return None
        idx = self._indices[entity_id]
        if idx < 0:
            return None
        return cast(np.double, self._data[idx])


class _PropertyFieldIndexerNoDataPointerNoBoundsCheck:
    def __init__(self, field: PropertyField):
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

    def by_id(self, entity_id: int) -> Optional[np.int64]:
        return cast(np.int64, self._data[self._indices[entity_id]])


class _PropertyFieldIndexerWithDataPointer:
    def __init__(self, field: PropertyField):
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._max_id = index_by_id.max_id

        self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)
        self._n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self._data) * self._n_components
        )

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
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


class _FieldIndexerWithDataPointer:
    def __init__(self, field: Field):
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping
        self._max_id = index_by_id.max_id

        self._data: NDArray[np.double] = np.array(field.data, dtype=np.double)
        self._n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self._data) * self._n_components
        )

    def by_id(self, entity_id: int) -> Optional[NDArray[np.double]]:
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


class _PropertyFieldIndexerWithDataPointerNoBoundsCheck:
    def __init__(self, field: PropertyField):
        index_by_id = _setup_index_by_id(field.scoping)
        self._indices = index_by_id.mapping

        self._data: NDArray[np.int64] = np.array(field.data, dtype=np.int64)

        self._n_components = field.component_count

        self._data_pointer: NDArray[np.int64] = np.append(
            field._data_pointer, len(self._data) * self._n_components
        )

    def by_id(self, entity_id: int) -> Optional[NDArray[np.int64]]:
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
