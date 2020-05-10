from __future__ import annotations

from typing import Generic

from .base import Base, IsCalculated, IsMulti, IsRelation, TEntity, With
from ..collections import ProtectedSet
from ..entity import Entity

__all__ = ['CalculatedMultiRelation']


class CalculatedMultiRelation(Generic[TEntity], Base[ProtectedSet[TEntity]], IsRelation, IsMulti, IsCalculated):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TEntity]:
        return ProtectedSet(__instance__=instance, __attr_name__=self._attr_name)
