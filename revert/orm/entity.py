from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, List, Type, TypeVar

from revert import Transaction

__all__ = ['Entity', 'UID']

TEntity = TypeVar('TEntity', bound='Entity')


class UID:
    val: str

    def __init__(self, **kwargs) -> None:
        if 'val' in kwargs:
            self.val = kwargs['val']
        else:
            self.val = str(uuid.uuid4())

    def __eq__(self, other: Any) -> bool:
        return self is other or (isinstance(other, UID) and other.val == self.val)

    def __hash__(self):
        return hash(self.val)

    def __str__(self):
        return self.val

    def __repr__(self):
        return f'UUID(val={self.val})'


class Entity(ABC):
    __class_reference__: str
    __uid__: UID
    __created_at__: datetime
    __updated_at__: datetime

    @property
    def uid(self) -> UID:
        return object.__getattribute__(self, '__uid__')

    @property
    def created_at(self) -> datetime:
        return object.__getattribute__(self, '__created_at__')

    @property
    def updated_at(self) -> datetime:
        return object.__getattribute__(self, '__updated_at__')

    def delete(self) -> None:
        orm.delete_object(self)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        orm.register_class(cls)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        orm.register_object(obj)
        return obj

    def __dir__(self) -> Iterable[str]:
        return orm.get_all_attrs(self)

    def __getattr__(self, attr: str) -> Any:
        return Transaction.get(orm.get_binding(self, attr))

    def __setattr__(self, attr: str, value: Any) -> None:
        Transaction.set(orm.get_binding(self, attr), orm.get_repr(value))

    def __repr__(self):
        return f'{self.__class__.__qualname__}.get_instance(\'{object.__getattribute__(self, "__uid__")}\')'

    def __eq__(self, other: Any) -> bool:
        return self is other or (isinstance(other, Entity) and object.__getattribute__(self, '__uid__') == object.__getattribute__(other, '__uid__'))

    def __hash__(self):
        return hash(object.__getattribute__(self, '__uid__'))

    @classmethod
    def get_instance(cls: Type[TEntity], uid: UID) -> TEntity:
        return orm.get_instance(uid)

    @classmethod
    def get(cls: Type[TEntity], *args, **kwargs) -> TEntity:
        pass

    def changed(self):
        pass

    @classmethod
    def class_reference(cls: Type[Entity]) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    @classmethod
    @abstractmethod
    def enforced_constraints(cls) -> List[constraints.Constraint]:
        pass


from . import orm, constraints
