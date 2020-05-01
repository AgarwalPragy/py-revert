from __future__ import annotations

from abc import ABC
from typing import Callable, List, TypeVar, Union

from .entity import Entity

__all__ = ['Constraint', 'ReverseOf', 'AutoAdd', 'Calculate', 'OnChange']

T = TypeVar('T')
TEntity = TypeVar('TEntity', bound=Entity)


class Constraint(ABC):
    pass


class ReverseOf(Constraint):
    def __init__(self, attr1: attributes.Descriptor, attr2: attributes.Descriptor) -> None:
        pass


class OnChange(Constraint):
    def __init__(self, attr, *, trigger: Callable[[TEntity], None]) -> None:
        pass


class AutoAdd(Constraint):
    def __init__(self, attr: attributes.Descriptor, *, to: attributes.Descriptor) -> None:
        pass


class Calculate(Constraint):
    def __init__(self, attr: attributes.Descriptor[T], *, based_on: Union[attributes.Descriptor, List[attributes.Descriptor]], formula: Callable[[TEntity], T]) -> None:
        pass


from . import attributes
