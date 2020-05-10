from __future__ import annotations

from typing import Generic

from .base import Base, TEntity, With
from ..collections import ProtectedSet
from ..entity import Entity

__all__ = ['UnionRelation']


class UnionRelation(Generic[TEntity], Base[ProtectedSet[TEntity]]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> ProtectedSet[TEntity]:
        pass
