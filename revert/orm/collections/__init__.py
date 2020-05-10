from __future__ import annotations

from typing import Any, Generic, Iterable, Set as tSet, TypeVar, Union

from revert import Transaction
from .. import orm
from ..entity import Entity

__all__ = ['Set', 'ProtectedSet']

primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes]
TValue = TypeVar('TValue', bound=Union[Entity, primitives])


class BaseSet(Generic[TValue]):
    __instance__: Entity
    __attr_name__: str
    __binding__: str

    def __init__(self, **kwargs) -> None:
        if '__instance__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__instance__ = kwargs['__instance__']
        self.__attr_name__ = kwargs['__attr_name__']
        self.__binding__ = orm.get_binding(self.__instance__, self.__attr_name__)

    def __iter__(self) -> Iterable[TValue]:
        pattern = f'{self.__binding__}/items'
        start = len(pattern) + 1
        for key in Transaction.match_keys(pattern):
            value = orm.get_value(key[start:])
            yield value

    def __contains__(self, item: TValue) -> bool:
        """ x.__contains__(y) <==> y in x. """
        return Transaction.has(f'{self.__binding__}/items/{orm.get_repr(item)}')

    def __len__(self) -> int:
        """ Return len(self). """
        return Transaction.match_count(f'{self.__binding__}/items')

    def __hash__(self) -> int:
        return hash(self.__binding__)

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        if isinstance(other, Set):
            return self.__binding__ == other.__binding__
        return list(self) == other

    def _add(self, item: TValue) -> None:
        Transaction.set(f'{self.__binding__}/items/{orm.get_repr(item)}', '')

    def _clear(self) -> None:
        for key in Transaction.match_keys(f'{self.__binding__}/items'):
            Transaction.delete(key)

    def _remove(self, item: TValue) -> None:
        Transaction.delete(f'{self.__binding__}/items/{orm.get_repr(item)}')

    def _discard(self, item: TValue) -> None:
        Transaction.discard(f'{self.__binding__}/items/{orm.get_repr(item)}')

    def copy(self) -> tSet[TValue]:
        return set(self)

    def _update(self, *items: tSet[TValue]) -> None:
        for collection in items:
            for item in collection:
                self._add(item)


class Set(BaseSet[TValue]):
    def add(self, item: TValue) -> None:
        self._add(item)

    def remove(self, item: TValue) -> None:
        self._remove(item)

    def update(self, *items: tSet[TValue]) -> None:
        self._update(*items)


class ProtectedSet(BaseSet[TValue]):
    pass
