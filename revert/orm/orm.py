from __future__ import annotations

# noinspection PyUnresolvedReferences
from datetime import datetime
from typing import Any, Dict, List, Type, Union, cast

from intent import Intent

from exceptions import *
from revert import Transaction, intent_db_connected
from . import config
from .entity import Entity, UID

__all__ = []

classes: Dict[str, Type[Entity]] = {}
object_cache: Dict[UID, Entity] = {}

intent_class_registered: Intent[Type[Entity]] = Intent()
intent_entity_created: Intent[Entity] = Intent()
intent_entity_before_delete: Intent[Entity] = Intent()


def db_connected(directory: str) -> None:
    with Transaction(message='schema change'):
        for cls in classes.values():
            mro = ','.join([parent.class_reference() for parent in cls.mro() if issubclass(parent, Entity)])
            Transaction.set(f'{config.base}/classes/{cls.class_reference()}/mro', mro)


def register_class(cls: Type[Entity]) -> None:
    class_reference = cls.class_reference()
    if class_reference in classes:
        raise ClassAlreadyRegisteredError(f'class with reference: {class_reference} has already been registered')
    classes[class_reference] = cls
    intent_class_registered.announce(cls)


def register_object(obj: Entity) -> None:
    class_reference = obj.__class__.class_reference()
    uid = UID()
    object.__setattr__(obj, '__uid__', uid)
    object.__setattr__(obj, '__class_reference__', class_reference)
    for cls in obj.__class__.mro():
        if issubclass(cls, Entity):
            Transaction.set(f'{config.base}/classes/{cls.class_reference()}/objects/{uid}', '')
    Transaction.set(f'{config.base}/objects/{uid}/class_reference', class_reference)
    Transaction.set(f'{config.base}/objects/{uid}/uid', str(uid))
    object_cache[uid] = obj
    intent_entity_created.announce(obj)


def delete_object(obj: Entity) -> None:
    intent_entity_before_delete.announce(obj)
    uid = object.__getattribute__(obj, '__uid__')
    class_reference = object.__getattribute__(obj, '__class_reference__')
    for key in Transaction.match_keys(f'{config.base}/objects/{uid}'):
        Transaction.delete(key)
    Transaction.delete(f'{config.base}/classes/{class_reference}/objects/{uid}')


def get_binding(obj: Entity, attr: str) -> str:
    uid = object.__getattribute__(obj, '__uid__')
    return f'{config.base}/objects/{uid}/attrs/{attr}'


def get_all_attrs(obj: Entity) -> List[str]:
    uid = object.__getattribute__(obj, '__uid__')
    trim_length = len(f'{config.base}/objects/{uid}/attrs/')
    return [key[trim_length:].split('/')[0] for key in Transaction.match_keys(f'{config.base}/objects/{uid}/attrs/')]


def get_instance(uid: Union[str, UID]) -> Entity:
    if isinstance(uid, str):
        uid = UID(val=uid)
    if uid in object_cache:
        return object_cache[uid]
    class_reference = Transaction.get(f'{config.base}/objects/{uid}/class_reference')
    cls = classes.get(class_reference, Entity)
    obj = cast(Entity, object.__new__(cls))
    object.__setattr__(obj, '__uid__', uid)
    object.__setattr__(obj, '__class_reference__', class_reference)
    return obj


def get_repr(item: Any) -> str:
    if isinstance(item, Entity):
        return f'get_instance(\'{object.__getattribute__(item, "__uid__")}\')'
    else:
        repr_ = repr(item)
        if repr_.strip().startswith('<'):
            raise UnsavableObjectError(f'object with rep: {repr_} cannot be saved without loss of data')
        return repr_


def get_value(repr_: str) -> Any:
    return eval(repr_)


intent_db_connected.subscribe(db_connected)
