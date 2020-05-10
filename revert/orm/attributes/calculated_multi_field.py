from __future__ import annotations

from typing import Generic

from .base import Base, Converter, IsCalculated, IsField, IsMulti, TPrimitive
from ..collections import ProtectedSet
from ..entity import Entity

__all__ = ['CalculatedMultiField']


class CalculatedMultiField(Generic[TPrimitive], Base[ProtectedSet[TPrimitive]], IsField, IsMulti, IsCalculated):
    converter: Converter

    def __init__(self, converter: Converter):
        self.converter = converter

    def _get_value(self, instance: Entity) -> ProtectedSet[TPrimitive]:
        return ProtectedSet(__instance__=instance, __attr_name__=self._attr_name)
