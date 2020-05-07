from __future__ import annotations

import uuid
from abc import ABC
from datetime import datetime
from typing import Any, Iterable, List, Type, TypeVar

from revert import Transaction

__all__ = ['Entity', 'UID']

T = TypeVar('T')
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


def clone(obj: T) -> T:
    copy = object.__new__(obj.__class__)
    copy.__dict__ = obj.__dict__.copy()
    return copy


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
        for attr_name in dir(cls):
            try:
                attr = getattr(cls, attr_name)
                if isinstance(attr, attributes.Descriptor):
                    if attr._owner_class != cls:
                        copy = clone(attr)
                        copy._owner_class = cls
                        setattr(cls, attr_name, copy)
            except Exception:
                pass
        orm.register_class(cls)

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
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
    def get(cls: Type[TEntity], **kwargs) -> TEntity:
        pass

    def changed(self):
        pass

    @classmethod
    def class_reference(cls: Type[Entity]) -> str:
        return f'{cls.__qualname__}'

    @classmethod
    def attribute_constraints(cls) -> List[constraints.Constraint]:
        return []


from . import orm, constraints, attributes
