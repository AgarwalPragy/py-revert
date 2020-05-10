from __future__ import annotations

from typing import Generic

from .base import Base, IsMulti, IsRelation, TEntity, With
from ..collections import Set
from ..entity import Entity

__all__ = ['MultiRelation']


class MultiRelation(Generic[TEntity], Base[Set[TEntity]], IsRelation, IsMulti):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> Set[TEntity]:
        return Set(__instance__=instance, __attr_name__=self._attr_name)
