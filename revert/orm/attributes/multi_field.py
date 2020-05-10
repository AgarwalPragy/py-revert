from __future__ import annotations

from typing import Generic

from .base import Base, Converter, IsField, IsMulti, TPrimitive
from ..collections import Set
from ..entity import Entity

__all__ = ['MultiField']


class MultiField(Generic[TPrimitive], Base[Set[TPrimitive]], IsField, IsMulti):
    converter: Converter

    def __init__(self, converter: Converter) -> None:
        self.converter = converter

    def _get_value(self, instance: Entity) -> Set[TPrimitive]:
        return Set(__instance__=instance, __attr_name__=self._attr_name)
