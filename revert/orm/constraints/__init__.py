from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Type, TypeVar

from intent import actor

from ..attributes.base import *
from ..entity import Entity

__all__ = ['Constraint',
           'Contributes', 'Reverse', 'OneToOne',
           'FormulaDependency',
           'OnChange',
           'FullTextSearch', 'Index', 'SortedIndex',
           'Volatile', 'Unique']

T = TypeVar('T')
TEntity = TypeVar('TEntity', bound=Entity)


class Constraint(ABC):
    @abstractmethod
    def __apply__(self, cls: Type[Entity]):
        pass


class Contributes(Constraint):
    attr: Base
    to: IsUnion

    def __init__(self, attr: Base, *, to: IsUnion) -> None:
        self.attr = attr
        self.to = to

    def __apply__(self, cls: Type[Entity]) -> None:
        self.attr.__add_contribution_contraint__(cls)


class Reverse(Constraint):
    attr1: IsRelation
    attr2: IsRelation

    def __init__(self, attr1: IsRelation, attr2: IsRelation) -> None:
        if not (isinstance(attr1, IsRelation) and isinstance(attr2, IsRelation)):
            raise TypeError('Reverse constraint can only be applied to Relations')
        self.attr1 = attr1
        self.attr2 = attr2

    def __apply__(self, cls: Type[Entity]):
        self.attr1.__add_reverse_constraint__(cls, self.attr2)
        self.attr2.__add_reverse_constraint__(cls, self.attr1)


class OneToOne(Constraint):
    attr1: IsRelation
    attr2: IsRelation

    def __init__(self, attr1: IsRelation, attr2: IsRelation) -> None:
        if not (isinstance(self.attr1, IsRelation) and isinstance(self.attr2, IsRelation)):
            raise TypeError('OneToOne constraint can only be applied to Relations')
        self.attr1 = attr1
        self.attr2 = attr2

    def __apply__(self, cls: Type[Entity]):
        self.attr1.__add_reverse_constraint__(cls, self.attr2)
        self.attr2.__add_reverse_constraint__(cls, self.attr1)


class OnChange(Constraint):
    attr: Base
    trigger: Callable[[TEntity], None]

    def __init__(self, attr: Base, *, trigger: Callable[[TEntity], None]) -> None:
        self.attr = attr
        self.trigger = trigger

    def __apply__(self, cls: Type[Entity]):
        self.attr.__add_change_constraint__(cls, self.trigger)


class FormulaDependency(Constraint):
    attr: IsCalculated
    dependency: Base

    def __init__(self, attr: IsCalculated, *, dependency: Base) -> None:
        self.attr = attr
        self.dependency = dependency

    def __apply__(self, cls: Type[Entity]):
        self.attr.__add_formula_constraint__(cls, self.trigger)


class FullTextSearch(ABC):
    def __init__(self, attr: IsField):
        pass

    def __apply__(self):
        pass


class Index(ABC):
    def __init__(self, attr: Base):
        pass

    def __apply__(self):
        pass


class SortedIndex(ABC):
    def __init__(self, attr: Base):
        pass

    def __apply__(self):
        pass


class Unique(ABC):
    def __init__(self, attr: Base):
        pass

    def __apply__(self):
        pass


class Volatile(ABC):
    def __init__(self, attr: Base):
        pass

    def __apply__(self):
        pass


@actor
def db_connected(directory: str) -> None:
    for cls in orm.classes.values():
        for constraint in cls.attribute_constraints():
            constraint.__apply__(cls)


from orm import orm
from revert import revert

revert.intent_db_connected.subscribe(db_connected)
