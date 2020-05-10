from __future__ import annotations

from typing import Generic

from revert import Transaction
from .base import Base, IsRelation, TEntity, With
from ..entity import Entity

__all__ = ['Relation']


class Relation(Generic[TEntity], Base[TEntity], IsRelation):
    
    def __init__(self, with_: With):
        pass

    def _get_value(self, instance: Entity) -> TEntity:
        return orm.get_value(Transaction.get(orm.get_binding(instance, self._attr_name)))

    def __set__(self, instance: Entity, value: TEntity) -> None:
        Transaction.set(orm.get_binding(instance, self._attr_name), orm.get_repr(value))

    def __add_reverse_constraint__(self, cls, to) -> None:
        pass


from .. import orm
