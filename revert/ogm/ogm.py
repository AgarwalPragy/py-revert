from __future__ import annotations

# noinspection PyUnresolvedReferences
import uuid
import datetime
from typing import Any, Dict as tDict, Optional, Type, cast

from intent import Intent

from revert import Transaction, intent_db_connected
from . import config
from .exceptions import ClassAlreadyRegisteredError, UnsavableObjectError
from .graph import Edge, Node

node_classes: tDict[str, Type[Node]] = {}
edge_classes: tDict[str, Type[Edge]] = {}
node_cache: tDict[str, Node] = {}

intent_class_registered: Intent[Type[Node]] = Intent()
intent_entity_created: Intent[Node] = Intent()
intent_entity_before_delete: Intent[Node] = Intent()


def db_connected(directory: str) -> None:
    with Transaction(message='schema change'):
        for cls in node_classes.values():
            mro = ','.join([parent.class_reference() for parent in cls.mro() if issubclass(parent, Node)])
            Transaction.put(f'{config.base}/classes/{cls.class_reference()}/mro', mro)


def register_node_class(cls: Type[Node]) -> None:
    class_reference = cls.class_reference()
    if class_reference in node_classes:
        raise ClassAlreadyRegisteredError(f'class with reference: {class_reference} has already been registered')
    node_classes[class_reference] = cls
    intent_class_registered.announce(cls)


def register_edge_class(cls: Type[Edge]) -> None:
    class_reference = cls.class_reference()
    if class_reference in edge_classes:
        raise ClassAlreadyRegisteredError(f'class with reference: {class_reference} has already been registered')
    edge_classes[class_reference] = cls
    intent_class_registered.announce(cls)


def register_node(obj: Node, uid: str) -> None:
    now = datetime.datetime.now()
    Transaction.put(f'{config.base}/objects/{uid}/created_at', encode(now))
    Transaction.put(f'{config.base}/objects/{uid}/updated_at', encode(now))
    object.__setattr__(obj, '__created_at__', now)
    object.__setattr__(obj, '__updated_at__', now)
    node_cache[uid] = obj
    intent_entity_created.announce(obj)


def update_node(obj: Optional[Node]) -> None:
    if obj is None:
        return
    now = datetime.datetime.now()
    uid = object.__getattribute__(obj, '__uid__')
    object.__setattr__(obj, '__updated_at__', now)
    Transaction.put(f'{config.base}/objects/{uid}/updated_at', encode(now))


def delete_node(obj: Node) -> None:
    intent_entity_before_delete.announce(obj)
    uid = object.__getattribute__(obj, '__uid__')
    if uid in node_cache:
        del node_cache[uid]


def get_node_binding(obj: Node, attr: str) -> str:
    uid = object.__getattribute__(obj, '__uid__')
    return f'{config.base}/objects/{uid}/attrs/{attr}'


def get_class_binding(cls: Type[Node], attr: str) -> str:
    return f'{config.base}/classes/{cls.class_reference()}/attrs/{attr}'


def get_node(uid: str) -> Node:
    if uid in node_cache:
        return node_cache[uid]
    class_reference = Transaction.get(f'{config.base}/objects/{uid}/class_reference')
    cls = node_classes.get(class_reference, Node)
    obj = cast(Node, object.__new__(cls))
    object.__setattr__(obj, '__uid__', uid)
    object.__setattr__(obj, '__class_reference__', class_reference)
    return obj


def encode(item: Any) -> str:
    if isinstance(item, Node):
        return f'get_node(\'{object.__getattribute__(item, "__uid__")}\')'
    elif isinstance(item, type) and issubclass(item, Node):
        return f'classes[\'{item.class_reference()}\']'
    else:
        repr_ = repr(item)
        if repr_.strip().startswith('<'):
            raise UnsavableObjectError(f'object with rep: {repr_} cannot be saved without loss of data')
        return repr_


def decode(repr_: str) -> Any:
    return eval(repr_)


intent_db_connected.subscribe(db_connected)
