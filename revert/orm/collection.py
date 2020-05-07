from __future__ import annotations

from typing import Any, Generic, Set as tSet, TypeVar, Union

from revert import Transaction
from . import orm
from .entity import Entity

__all__ = ['Set', 'ProtectedSet']

primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes]
TValue = TypeVar('TValue', bound=Union[Entity, primitives])


class BaseSet(Generic[TValue]):
    __instance__: Entity
    __attr_name__: str
    __binding__: str

    def __init__(self, **kwargs):
        if '__instance__' not in kwargs:
            raise TypeError(f'Cannot instantiate of object of {self.__class__.__name__}')
        self.__instance__ = kwargs['__instance__']
        self.__attr_name__ = kwargs['__attr_name__']
        self.__binding__ = orm.get_binding(self.__instance__, self.__attr_name__)

    def __iter__(self):
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

    def __hash__(self):
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

    def _pop(self) -> TValue:
        """
        Remove and return an arbitrary set element.
        Raises KeyError if the set is empty.
        """

    def _remove(self, item: TValue) -> None:
        """
        Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        Transaction.delete(f'{self.__binding__}/items/{orm.get_repr(item)}')

    def _discard(self, item: TValue) -> None:
        """
        Remove an element from a set if it is a member.

        If the element is not a member, do nothing.
        """
        Transaction.delete(f'{self.__binding__}/items/{orm.get_repr(item)}', ignore_if_not_present=True)

    def copy(self) -> tSet[TValue]:
        return set(self)

    def difference(self, *items: tSet[TValue]) -> tSet[TValue]:
        """
        Return the difference of two or more sets as a new set.
        (i.e. all elements that are in this set but not the others.)
        """
        diff = self.copy()
        for item in items:
            diff -= item
        return diff

    def intersection(self, *items: tSet[TValue]) -> tSet[TValue]:
        """
        Return the intersection of two sets as a new set.

        (i.e. all elements that are in both sets.)
        """
        intersect = self.copy()
        for item in items:
            intersect &= item
        return intersect

    def isdisjoint(self, *args, **kwargs):
        """ Return True if two sets have a null intersection. """

    def issubset(self, *args, **kwargs):
        """ Report whether another set contains this set. """

    def issuperset(self, *args, **kwargs):
        """ Report whether this set contains another set. """

    def symmetric_difference(self, *args, **kwargs):
        """
        Return the symmetric difference of two sets as a new set.

        (i.e. all elements that are in exactly one of the sets.)
        """

    def symmetric_difference_update(self, *args, **kwargs):
        """ Update a set with the symmetric difference of itself and another. """

    def union(self, *args, **kwargs):
        """
        Return the union of sets as a new set.

        (i.e. all elements that are in either set.)
        """

    def _update(self, *items: tSet[TValue]) -> None:
        """ Update a set with the union of itself and others. """
        for collection in items:
            for item in collection:
                self._add(item)

    def __and__(self, *args, **kwargs):
        """ Return self&value. """

    def __ge__(self, *args, **kwargs):
        """ Return self>=value. """

    def __gt__(self, *args, **kwargs):
        """ Return self>value. """

    def __le__(self, *args, **kwargs):
        """ Return self<=value. """

    def __lt__(self, *args, **kwargs):
        """ Return self<value. """

    def __ne__(self, *args, **kwargs):
        """ Return self!=value. """

    def __or__(self, *args, **kwargs):
        """ Return self|value. """

    def __rand__(self, *args, **kwargs):
        """ Return value&self. """

    def __reduce__(self, *args, **kwargs):
        """ Return state information for pickling. """

    def __repr__(self, *args, **kwargs):
        """ Return repr(self). """

    def __ror__(self, *args, **kwargs):
        """ Return value|self. """

    def __rsub__(self, *args, **kwargs):
        """ Return value-self. """

    def __rxor__(self, *args, **kwargs):
        """ Return value^self. """

    def __sub__(self, *args, **kwargs):
        """ Return self-value. """

    def __xor__(self, *args, **kwargs):
        """ Return self^value. """


class Set(BaseSet[TValue]):
    def add(self, item: TValue) -> None:
        self._add(item)

    def remove(self, item: TValue) -> None:
        self._remove(item)

    def difference_update(self, *items: tSet[TValue]) -> None:
        """ Remove all elements of another set from this set. """
        self._clear()
        for item in self.difference(*items):
            self.add(item)

    def intersection_update(self, *items: tSet[TValue]) -> None:
        """ Update a set with the intersection of itself and another. """
        self._clear()
        for item in self.intersection(*items):
            self.add(item)

    def update(self, *items: tSet[TValue]) -> None:
        """ Update a set with the union of itself and others. """
        self._update(*items)

    def __iand__(self, *args, **kwargs):
        """ Return self&=value. """

    def __ior__(self, *args, **kwargs):
        """ Return self|=value. """

    def __isub__(self, *args, **kwargs):
        """ Return self-=value. """

    def __ixor__(self, *args, **kwargs):
        """ Return self^=value. """


class ProtectedSet(BaseSet[TValue]):
    pass
