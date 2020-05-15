from __future__ import annotations

from typing import AbstractSet, Any, Dict as tDict, Iterable, Iterator, List, Mapping, MutableMapping, MutableSet, Set as tSet, Tuple, TypeVar, overload

from revert import Transaction

__all__ = ['Set', 'ProtectedSet', 'Dict', 'ProtectedDict']

TKey = TypeVar('TKey')
TVal = TypeVar('TVal')


class BaseSet(AbstractSet[TVal]):
    __binding__: str

    def __init__(self, **kwargs) -> None:
        if '__binding__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__binding__ = kwargs['__binding__']

    def __iter__(self) -> Iterator[TVal]:
        pattern = f'{self.__binding__}'
        start = len(pattern) + 1
        for key in Transaction.match_keys(pattern):
            value = ogm.decode(key[start:])
            yield value

    def __contains__(self, item: Any) -> bool:
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
        return list(self) == list(other)

    def copy(self) -> tSet[TVal]:
        return set(self)


class Set(BaseSet[TVal], MutableSet[TVal]):
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


class ProtectedSet(BaseSet[TVal]):
    pass


class BaseDict(Mapping[TKey, TVal]):
    __binding__: str

    def __init__(self, **kwargs) -> None:
        if '__binding__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__binding__ = kwargs['__binding__']

    def keys(self) -> AbstractSet[TKey]:
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

    def __contains__(self, item: Any) -> bool:
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


class Dict(BaseDict[TKey, TVal], MutableMapping[TKey, TVal]):
    def __setitem__(self, key: TKey, value: TVal) -> None:
        Transaction.set(f'{self.__binding__}/{ogm.encode(key)}', ogm.encode(value))

    def __delitem__(self, key: TKey) -> None:
        Transaction.delete(f'{self.__binding__}/{ogm.encode(key)}')

    def clear(self) -> None:
        for key in Transaction.match_keys(f'{self.__binding__}'):
            Transaction.delete(key)

    @overload
    def update(self, __m: Mapping, **kwargs: Any) -> None:
        ...

    @overload
    def update(self, __m: Iterable[Tuple[Any, Any]], **kwargs: Any) -> None:
        ...

    @overload
    def update(self, **kwargs: Any) -> None:
        ...

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value


class ProtectedDict(BaseDict[TKey, TVal], Mapping[TKey, TVal]):
    pass


from . import ogm
