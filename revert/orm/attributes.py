from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Generic, Literal, Optional, overload, Type, TypeVar, Union

from revert import Transaction
from .collection import ProtectedSet, Set
from .entity import Entity

__all__ = ['Field', 'ProtectedField', 'MultiField', 'ProtectedMultiField',
           'Relation', 'ProtectedRelation', 'MultiRelation', 'ProtectedMultiRelation']

primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes, datetime]
T = TypeVar('T')
TPrimitive = TypeVar('TPrimitive', bound=primitives)
TEntity = TypeVar('TEntity', bound=Entity)
TValue = TypeVar('TValue', bound=Union[Entity, primitives])
Converter = Callable[[Any], TPrimitive]
With = Callable[[], Type[TEntity]]
TDescriptor = TypeVar('TDescriptor', bound='Descriptor')


class Descriptor(Generic[T], ABC):
    _attr_name: str
    _owner_class: Type[Entity]

    def __set_name__(self, owner: Type[Entity], name: str) -> None:
        self._attr_name = name
        self._owner_class = owner

    @overload
    def __get__(self: TDescriptor, instance: Literal[None], owner: Type[Entity]) -> TDescriptor:
        ...

    @overload
    def __get__(self: TDescriptor, instance: Entity, owner: Type[Entity]) -> T:
        ...

    def __get__(self: TDescriptor, instance: Optional[Entity], owner: Type[Entity]) -> Union[TDescriptor, T]:
        if instance is None:
            return self
        return self._get_value(instance)

    @abstractmethod
    def _get_value(self, instance: Entity) -> T:
        ...


# todo: add support for volatile fields

class Field(Generic[TPrimitive], Descriptor[TPrimitive]):
    def __init__(self, converter: Converter, volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> TPrimitive:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Entity, value: TPrimitive) -> None:
        Transaction.set(orm.get_binding(instance, self._attr_name), orm.get_repr(value))


class ProtectedField(Generic[TPrimitive], Descriptor[TPrimitive]):
    def __init__(self, converter: Converter, volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> TPrimitive:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))


class MultiField(Generic[TPrimitive], Descriptor[Set[TPrimitive]]):
    def __init__(self, converter: Converter, volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> Set[TPrimitive]:
        return Set(__instance__=instance, __attr_name__=self._attr_name)


class ProtectedMultiField(Generic[TPrimitive], Descriptor[ProtectedSet[TPrimitive]]):
    def __init__(self, converter: Converter, volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TPrimitive]:
        return ProtectedSet(__instance__=instance, __attr_name__=self._attr_name)


class Relation(Generic[TEntity], Descriptor[TEntity]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Entity, value: TEntity) -> None:
        Transaction.set(orm.get_binding(instance, self._attr_name), orm.get_repr(value))


class ProtectedRelation(Generic[TEntity], Descriptor[TEntity]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))


class MultiRelation(Generic[TEntity], Descriptor[Set[TEntity]]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> Set[TEntity]:
        return Set(__instance__=instance, __attr_name__=self._attr_name)


class ProtectedMultiRelation(Generic[TEntity], Descriptor[ProtectedSet[TEntity]]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TEntity]:
        return ProtectedSet(__instance__=instance, __attr_name__=self._attr_name)


from . import orm
