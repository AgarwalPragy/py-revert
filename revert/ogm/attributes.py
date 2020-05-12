from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Literal, Optional, Type, TypeVar, Union, overload

from revert import Transaction
from .collections import Dict, Set
from .graph import Node

__all__ = ['Field', 'SetField', 'DictField', 'ClassField', 'ClassDictField', 'ClassSetField']

T = TypeVar('T')
TKey = TypeVar('TKey')
TVal = TypeVar('TVal')
TBase = TypeVar('TBase', bound='Base')
TClassBase = TypeVar('TClassBase', bound='ClassBase')


class Base(Generic[T], ABC):
    _attr_name: str
    _owner_class: Type[Node]

    def __set_name__(self, owner: Type[Node], name: str) -> None:
        self._attr_name = name
        self._owner_class = owner

    @overload
    def __get__(self: TBase, instance: Literal[None], owner: Type[Node]) -> TBase:
        ...

    @overload
    def __get__(self: TBase, instance: Node, owner: Type[Node]) -> T:
        ...

    def __get__(self: TBase, instance: Optional[Node], owner: Type[Node]) -> Union[TBase, T]:
        if instance is None:
            return self
        return self._get_value(instance)

    @abstractmethod
    def _get_value(self, instance: Node) -> T:
        ...


class ClassBase(Generic[T], ABC):
    _attr_name: str
    _owner_class: Type[Node]

    def __set_name__(self, owner: Type[Node], name: str) -> None:
        self._attr_name = name
        self._owner_class = owner

    @overload
    def __get__(self: TClassBase, instance: Literal[None], owner: Type[Node]) -> TClassBase:
        ...

    @overload
    def __get__(self: TClassBase, instance: Node, owner: Type[Node]) -> T:
        ...

    def __get__(self: TClassBase, instance: Optional[Node], owner: Type[Node]) -> Union[TClassBase, T]:
        if instance is None:
            return self
        return self._get_value(instance)

    @abstractmethod
    def _get_value(self, instance: Node) -> T:
        ...


class Field(Generic[TVal], Base[TVal]):
    def _get_value(self, instance: Node) -> TVal:
        return ogm.decode(Transaction.get(ogm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Node, value: TVal) -> None:
        Transaction.set(ogm.get_binding(instance, self._attr_name), ogm.encode(value))


class ClassField(Generic[TVal], ClassBase[TVal]):
    def _get_value(self, instance: Node) -> TVal:
        return ogm.decode(Transaction.get(ogm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Node, value: TVal) -> None:
        Transaction.set(ogm.get_binding(instance, self._attr_name), ogm.encode(value))


class SetField(Generic[TVal], Base[Set[TVal]]):
    def _get_value(self, instance: Node) -> Set[TVal]:
        return Set(__binding__=ogm.get_binding(instance, self._attr_name))


class ClassSetField(Generic[TVal], ClassBase[Set[TVal]]):
    def _get_value(self, instance: Node) -> Set[TVal]:
        return Set(__binding__=ogm.get_binding(instance, self._attr_name))


class DictField(Generic[TKey, TVal], Base[Dict[TKey, TVal]]):
    def _get_value(self, instance: Node) -> Dict[TKey, TVal]:
        return Dict(__binding__=ogm.get_binding(instance, self._attr_name))


class ClassDictField(Generic[TKey, TVal], ClassBase[Dict[TKey, TVal]]):
    def _get_value(self, instance: Node) -> Dict[TKey, TVal]:
        return Dict(__binding__=ogm.get_binding(instance, self._attr_name))


from . import ogm
