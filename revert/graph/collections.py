from __future__ import annotations

from typing import Any, Dict as tDict, Generic, Iterable, List, Set as tSet, Tuple, TypeVar

from revert import Transaction
from . import ogm

__all__ = ['Set', 'ProtectedSet', 'Dict', 'ProtectedDict']

TKey = TypeVar('TKey')
TVal = TypeVar('TVal')


class BaseSet(Generic[TVal]):
    __binding__: str

    def __init__(self, **kwargs) -> None:
        if '__binding__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__binding__ = kwargs['__binding__']

    def __iter__(self) -> Iterable[TVal]:
        pattern = f'{self.__binding__}'
        start = len(pattern) + 1
        for key in Transaction.match_keys(pattern):
            value = ogm.decode(key[start:])
            yield value

    def __contains__(self, item: TVal) -> bool:
        """ x.__contains__(y) <==> y in x. """
        return Transaction.has(f'{self.__binding__}/{ogm.encode(item)}')

    def __len__(self) -> int:
        """ Return len(self). """
        return Transaction.match_count(f'{self.__binding__}')

    def __hash__(self) -> int:
        return hash(self.__binding__)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        if isinstance(other, Set):
            return self.__binding__ == other.__binding__
        return list(self) == other

    def copy(self) -> tSet[TVal]:
        return set(self)


class Set(BaseSet[TVal], Generic[TVal]):
    def add(self, item: TVal) -> None:
        Transaction.set(f'{self.__binding__}/{ogm.encode(item)}', '')

    def clear(self) -> None:
        for key in Transaction.match_keys(f'{self.__binding__}'):
            Transaction.delete(key)

    def remove(self, item: TVal) -> None:
        Transaction.delete(f'{self.__binding__}/{ogm.encode(item)}')

    def discard(self, item: TVal) -> None:
        Transaction.discard(f'{self.__binding__}/{ogm.encode(item)}')

    def update(self, *items: tSet[TVal]) -> None:
        for collection in items:
            for item in collection:
                self.add(item)


class ProtectedSet(BaseSet[TVal], Generic[TVal]):
    pass


class BaseDict(Generic[TKey, TVal], Generic[TKey, TVal]):
    __binding__: str

    def __init__(self, **kwargs) -> None:
        if '__binding__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__binding__ = kwargs['__binding__']

    def keys(self) -> List[TKey]:
        pattern = f'{self.__binding__}'
        start = len(pattern) + 1
        for key in Transaction.match_keys(pattern):
            k = ogm.decode(key[start:])
            yield k

    def values(self) -> List[TVal]:
        pattern = f'{self.__binding__}'
        for _, value in Transaction.match_items(pattern):
            v = ogm.decode(value)
            yield v

    def items(self) -> List[Tuple[TKey, TVal]]:
        pattern = f'{self.__binding__}'
        start = len(pattern) + 1
        for key, value in Transaction.match_items(pattern):
            k = ogm.decode(key[start:])
            v = ogm.decode(value)
            yield k, v

    def __getitem__(self, key: TKey) -> TVal:
        return ogm.decode(Transaction.get(f'{self.__binding__}/{ogm.encode(key)}'))

    def __iter__(self) -> Iterable[TKey]:
        return self.keys()

    def __contains__(self, item: TKey) -> bool:
        """ x.__contains__(y) <==> y in x. """
        return Transaction.has(f'{self.__binding__}/{ogm.encode(item)}')

    def __len__(self) -> int:
        """ Return len(self). """
        return Transaction.match_count(f'{self.__binding__}')

    def __hash__(self) -> int:
        return hash(self.__binding__)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        if isinstance(other, Set):
            return self.__binding__ == other.__binding__
        return list(self) == other

    def copy(self) -> tDict[TKey, TVal]:
        return {key: value for key, value in self.items()}


class Dict(BaseDict[TKey, TVal]):
    def __setitem__(self, key: TKey, value: TVal) -> None:
        Transaction.set(f'{self.__binding__}/{ogm.encode(key)}', ogm.encode(value))

    def __delitem__(self, key: TKey) -> None:
        Transaction.delete(f'{self.__binding__}/{ogm.encode(key)}')

    def clear(self) -> None:
        for key in Transaction.match_keys(f'{self.__binding__}'):
            Transaction.delete(key)

    def update(self, *items: tDict[TKey, TVal]) -> None:
        for collection in items:
            for key, value in collection.items():
                self[key] = value


class ProtectedDict(BaseDict[TKey, TVal]):
    pass
