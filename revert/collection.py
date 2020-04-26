from __future__ import annotations
from typing import Generic, TypeVar, Union

from .entity import Entity

__all__ = ['Set', 'ProtectedSet']

primitives = Union[str, int, bool, float, None, complex, frozenset, tuple, bytes]
TValue = TypeVar('TValue', bound=Union[Entity, primitives])


class Set(Generic[TValue]):
    pass


class ProtectedSet(Generic[TValue]):
    pass
