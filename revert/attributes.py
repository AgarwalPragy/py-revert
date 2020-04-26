from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Literal, Optional, overload, Type, TypeVar, Union

from .collection import ProtectedSet, Set
from .entity import Entity

__all__ = ['Field', 'ProtectedField', 'MultiField', 'ProtectedMultiField',
           'Relation', 'ProtectedRelation', 'MultiRelation', 'ProtectedMultiRelation',
           'Constraint', 'ReverseOf', 'AutoAdd', 'Calculate', 'OnChange']

primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes]
T = TypeVar('T')
TPrimitive = TypeVar('TPrimitive', bound=primitives)
TEntity = TypeVar('TEntity', bound='Entity')
TValue = TypeVar('TValue', bound=Union['Entity', primitives])
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
    def __init__(self, converter: Converter[TPrimitive], volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> TPrimitive:
        return instance.__dict__[self._attr_name]

    def __set__(self, instance: Entity, value: TPrimitive) -> None:
        core.set_attr(instance, self._attr_name, value)
        instance.__dict__[self._attr_name] = value


class ProtectedField(Generic[TPrimitive], Descriptor[TPrimitive]):
    def __init__(self, converter: Converter[TPrimitive], volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> TPrimitive:
        return instance.__dict__[self._attr_name]


class MultiField(Generic[TPrimitive], Descriptor[Set[TPrimitive]]):
    def __init__(self, converter: Converter[TPrimitive], volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> Set[TPrimitive]:
        pass


class ProtectedMultiField(Generic[TPrimitive], Descriptor[ProtectedSet[TPrimitive]]):
    def __init__(self, converter: Converter[TPrimitive], volatile: bool = False, index: bool = False, unique: bool = False, full_text_search: bool = False):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TPrimitive]:
        pass


class Relation(Generic[TEntity], Descriptor[TEntity]):
    def __init__(self, with_: With[TEntity]):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        pass

    def __set__(self, instance: Entity, value: TEntity) -> None:
        return instance.__dict__[self._attr_name]


class ProtectedRelation(Generic[TEntity], Descriptor[TEntity]):
    def __init__(self, with_: With[TEntity]):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        return instance.__dict__[self._attr_name]


class MultiRelation(Generic[TEntity], Descriptor[Set[TEntity]]):
    def __init__(self, with_: With[TEntity]):
        pass

    def _get_value(self, instance: Entity) -> Set[TEntity]:
        pass


class ProtectedMultiRelation(Generic[TEntity], Descriptor[ProtectedSet[TEntity]]):
    def __init__(self, with_: With[TEntity]):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TEntity]:
        pass


class Constraint(ABC):
    pass


class ReverseOf(Constraint):
    def __init__(self, attr1: Descriptor, attr2: Descriptor) -> None:
        pass


class OnChange(Constraint):
    def __init__(self, attr, *, trigger: Callable[[TEntity], None]) -> None:
        pass


class AutoAdd(Constraint):
    def __init__(self, attr: Descriptor, *, to: Descriptor) -> None:
        pass


class Calculate(Constraint):
    def __init__(self, attr: Descriptor[T], *, based_on: Union[Descriptor, List[Descriptor]], formula: Callable[[TEntity], T]) -> None:
        pass


from . import core
