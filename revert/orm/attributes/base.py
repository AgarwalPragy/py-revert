from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Generic, Literal, Optional, Type, TypeVar, Union, overload

from ..entity import Entity

__all__ = ['Base',
           'IsRelation', 'IsField', 'IsCalculated', 'IsProtected', 'IsMulti', 'IsSingle', 'IsUnion',
           'T', 'TPrimitive', 'TEntity', 'TValue', 'Converter', 'With']

T = TypeVar('T')
TBase = TypeVar('TBase', bound='Descriptor')
primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes, datetime]
TPrimitive = TypeVar('TPrimitive', bound=primitives)
TEntity = TypeVar('TEntity', bound=Entity)
TValue = TypeVar('TValue', bound=Union[Entity, primitives])
Converter = Callable[[Any], TPrimitive]
With = Callable[[], Type[TEntity]]


class Base(Generic[T], ABC):
    _attr_name: str
    _owner_class: Type[Entity]

    def __set_name__(self, owner: Type[Entity], name: str) -> None:
        self._attr_name = name
        self._owner_class = owner

    @overload
    def __get__(self: TBase, instance: Literal[None], owner: Type[Entity]) -> TBase:
        ...

    @overload
    def __get__(self: TBase, instance: Entity, owner: Type[Entity]) -> T:
        ...

    def __get__(self: TBase, instance: Optional[Entity], owner: Type[Entity]) -> Union[TBase, T]:
        if instance is None:
            return self
        return self._get_value(instance)

    @abstractmethod
    def _get_value(self, instance: Entity) -> T:
        ...


class IsField:
    pass


class IsRelation:
    pass


class IsSingle:
    pass


class IsMulti:
    pass


class IsUnion:
    pass


class IsCalculated:
    pass


class IsProtected:
    pass
