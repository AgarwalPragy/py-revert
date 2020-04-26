from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, List, Type, TypeVar

__all__ = ['Entity']

TEntity = TypeVar('TEntity', bound='Entity')


class Entity(ABC):
    __class_reference__: str = ''
    __uid__: int
    __created_at__: datetime
    __updated_at__: datetime

    @property
    def uid(self) -> int:
        return object.__getattribute__(self, '__uid__')

    @property
    def created_at(self) -> datetime:
        return object.__getattribute__(self, '__created_at__')

    @property
    def updated_at(self) -> datetime:
        return object.__getattribute__(self, '__updated_at__')

    def delete(self) -> None:
        core.delete_object(self)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        core.register_class(cls)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        core.register_object(obj)
        return obj

    def __dir__(self) -> Iterable[str]:
        return core.get_all_attrs(self)

    def __getattr__(self, attr: str) -> Any:
        return core.get_attr(self, attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        core.set_attr(self, attr, value)

    def __repr__(self):
        return f'{self.__class__.__qualname__}.get_instance({object.__getattribute__(self, "__uid__")})'

    def __eq__(self, other: Any) -> bool:
        return self is other or (isinstance(other, Entity) and object.__getattribute__(self, '__uid__') == object.__getattribute__(other, '__uid__'))

    def __hash__(self):
        return hash(object.__getattribute__(self, '__uid__'))

    @classmethod
    def get_instance(cls, uid: int) -> Entity:
        return core.get_instance(cls, uid)

    @classmethod
    def get(cls: Type[TEntity], *args, **kwargs) -> TEntity:
        pass

    def changed(self):
        pass

    @classmethod
    @abstractmethod
    def enforced_constraints(cls) -> List[attributes.Constraint]:
        pass


from . import core
from . import attributes
