from __future__ import annotations

from typing import Generic

from .base import Base, TEntity, With
from ..entity import Entity

__all__ = ['BackReference']


class BackReference(Generic[TEntity], Base[TEntity]):
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        pass
