from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, TypeVar

from intent import actor

from .entity import Entity

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
    def __apply__(self):
        pass


class Contributes(Constraint):
    attr: attributes.Descriptor
    to: attributes.UnionRelation

    def __init__(self, attr: attributes.Descriptor, *, to: attributes.UnionRelation) -> None:
        self.attr = attr
        self.to = to

    def __apply__(self):
        pass


class Reverse(Constraint):
    attr1: attributes.IsRelation
    attr2: attributes.IsRelation

    def __init__(self, attr1: attributes.IsRelation, attr2: attributes.IsRelation) -> None:
        self.attr1 = attr1
        self.attr2 = attr2

    def __apply__(self):
        if not (isinstance(self.attr1, attributes.IsRelation) and isinstance(self.attr2, attributes.IsRelation)):
            raise TypeError('Reverse constraint can only be applied to Relations')
        # self.attr1.__add_reverse_constraint__(self.attr2)
        # self.attr2.__add_reverse_constraint__(self.attr1)


class OneToOne(Constraint):
    attr1: attributes.IsRelation
    attr2: attributes.IsRelation

    def __init__(self, attr1: attributes.IsRelation, attr2: attributes.IsRelation) -> None:
        self.attr1 = attr1
        self.attr2 = attr2

    def __apply__(self):
        if not (isinstance(self.attr1, attributes.IsRelation) and isinstance(self.attr2, attributes.IsRelation)):
            raise TypeError('OneToOne constraint can only be applied to Relations')


class OnChange(Constraint):
    attr: attributes.Descriptor
    trigger: Callable[[TEntity], None]

    def __init__(self, attr: attributes.Descriptor, *, trigger: Callable[[TEntity], None]) -> None:
        self.attr = attr
        self.trigger = trigger

    def __apply__(self):
        pass


class FormulaDependency(Constraint):
    attr: attributes.IsCalculated
    dependency: attributes.Descriptor

    def __init__(self, attr: attributes.IsCalculated, *, dependency: attributes.Descriptor) -> None:
        self.attr = attr
        self.dependency = dependency

    def __apply__(self):
        pass


class FullTextSearch(ABC):
    def __init__(self, attr: attributes.IsField):
        pass

    def __apply__(self):
        pass


class Index(ABC):
    def __init__(self, attr: attributes.Descriptor):
        pass

    def __apply__(self):
        pass


class SortedIndex(ABC):
    def __init__(self, attr: attributes.Descriptor):
        pass

    def __apply__(self):
        pass


class Unique(ABC):
    def __init__(self, attr: attributes.Descriptor):
        pass

    def __apply__(self):
        pass


class Volatile(ABC):
    def __init__(self, attr: attributes.Descriptor):
        pass

    def __apply__(self):
        pass


@actor
def db_connected(directory: str) -> None:
    for cls in orm.classes.values():
        for constraint in cls.attribute_constraints():
            constraint.__apply__()


from . import attributes
from . import orm
from revert import revert

revert.intent_db_connected.subscribe(db_connected)
