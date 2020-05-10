from __future__ import annotations

from typing import Generic

from revert import Transaction
from .base import Base, Converter, IsCalculated, IsField, TPrimitive
from ..entity import Entity

__all__ = ['CalculatedField']


class CalculatedField(Generic[TPrimitive], Base[TPrimitive], IsField, IsCalculated):
    converter: Converter

    def __init__(self, converter: Converter) -> None:
        self.converter = converter

    def _get_value(self, instance: Entity) -> TPrimitive:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))


from .. import orm
