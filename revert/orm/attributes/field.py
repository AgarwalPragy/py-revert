from __future__ import annotations

from typing import Generic

from revert import Transaction
from .base import Base, Converter, IsField, IsSingle, TPrimitive
from ..entity import Entity

__all__ = ['Field']


class Field(Generic[TPrimitive], Base[TPrimitive], IsField, IsSingle):
    converter: Converter

    def __init__(self, converter: Converter):
        self.converter = converter

    def _get_value(self, instance: Entity) -> TPrimitive:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Entity, value: TPrimitive) -> None:
        Transaction.set(orm.get_binding(instance, self._attr_name), orm.get_repr(value))


from .. import orm
