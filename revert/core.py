from __future__ import annotations

from copy import deepcopy
from functools import wraps
from typing import Any, ClassVar, Dict, List, Type

# from utils import Signal

from .entity import Entity
from .exceptions import *

__all__ = ['current_commit', 'connect', 'Transaction', 'rollback', 'checkout', 'undo', 'redo']

_db_null = object()

current_commit: str = 'HEAD'

dir_: str = None
data: Dict[str, Dict[int, Dict[str, Any]]] = {}  # class_reference -> object_uid -> attribute -> value
uid_sequence: Dict[str, int] = {}
classes: Dict[str, Type[Entity]] = {}


def register_class(cls: Type[Entity]) -> None:
    class_reference = _get_class_reference(cls)
    if class_reference in classes:
        raise ClassAlreadyRegisteredError(f'class with reference: {class_reference} has already been registered')
    classes[class_reference] = cls
    uid_sequence[class_reference] = 0
    data[class_reference] = {}
    Transaction.dirty[class_reference] = {}


def register_object(obj: Entity) -> None:
    class_reference = _get_class_reference(obj.__class__)
    uid = uid_sequence[class_reference] + 1
    object.__setattr__(obj, '__uid__', uid)
    uid_sequence[class_reference] = uid
    Transaction.dirty[class_reference][uid] = {'__uid__': uid}


def delete_object(obj: Entity) -> None:
    class_reference = _get_class_reference(obj.__class__)
    uid = object.__getattribute__(obj, '__uid__')
    for attr in data[class_reference][uid]:
        Transaction.current_transaction().dirty[class_reference][uid] = {attr: _db_null}
    Transaction.current_transaction().dirty[class_reference][uid] = {'__uid__': _db_null}


def set_attr(obj: Entity, attr: str, value: Any) -> None:
    class_reference = _get_class_reference(obj.__class__)
    uid = object.__getattribute__(obj, '__uid__')
    Transaction.current_transaction().dirty[class_reference][uid][attr] = _get_repr(value)


def get_attr(obj: Entity, attr: str) -> Any:
    class_reference = _get_class_reference(obj.__class__)
    uid = object.__getattribute__(obj, '__uid__')
    value = Transaction.current_transaction().dirty.get(class_reference, {}).get(uid, {}).get(attr, _db_null)
    if value == _db_null:
        value = data.get(class_reference, {}).get(uid, {}).get(attr, _db_null)
    if value == _db_null:
        raise AttributeError(attr)
    return value


def get_all_attrs(self):
    return None


def get_instance(cls: Type[Entity], uid: int) -> Entity:
    return _get_instance(_get_class_reference(cls), uid)


def connect(directory: str) -> None:
    global dir_
    dir_ = directory


class Transaction:
    running_transactions: ClassVar[List[Transaction]] = []
    messages: ClassVar[List[str]] = []
    dirty: Dict[str, Dict[int, Dict[str, Any]]] = {}  # class_reference -> object_uid -> attribute -> value

    msg: str
    rollback_on_error: bool
    dirty_before_me: Dict[str, Dict[int, Dict[str, Any]]] = {}  # class_reference -> object_uid -> attribute -> value

    @staticmethod
    def add_message(self, message: str):
        pass

    @staticmethod
    def current_transaction() -> Transaction:
        if not Transaction.running_transactions:
            raise NoTransactionActiveError('Entity attributes are only accessible while inside a Transaction')
        return Transaction.running_transactions[-1]

    def __init__(self, message: str = '', rollback_on_error: bool = False):
        self.msg = message
        self.rollback_on_error = rollback_on_error

    def __call__(self, func, *, message: str = '', rollback_on_error: bool = False):
        @wraps
        def wrapped(*args, **kwargs):
            with Transaction(message=message, rollback_on_error=rollback_on_error) as t:
                func(*args, **kwargs)

        return wrapped

    def __enter__(self):
        Transaction.running_transactions.append(self)
        Transaction.messages.append(self.msg)
        self.dirty_before_me = deepcopy(Transaction.dirty)

    def __exit__(self, exc_type, exc_val, exc_tb):
        Transaction.running_transactions.pop()
        if not Transaction:
            Transaction.force_commit()

    @staticmethod
    def force_commit():
        pass


def rollback(rollback_all: bool = False) -> None:
    if rollback_all:
        Transaction.running_transactions = []
        Transaction.messages = []
        Transaction.dirty = {}
    else:
        Transaction.dirty = deepcopy(Transaction.current_transaction().dirty_before_me)


def checkout(commit_id: str) -> None:
    pass


def undo() -> None:
    pass


def redo() -> None:
    pass


def _get_class_reference(cls: Type[Entity]) -> str:
    class_reference = cls.__class_reference__
    if not class_reference:
        class_reference = f'{cls.__module__}.{cls.__qualname__}'
    return class_reference


def _get_key(obj: Entity, attr: str) -> str:
    return f'{_get_class_reference(obj.__class__)} -> {_get_repr(attr)}'


def _get_class(class_reference: str) -> Type[Entity]:
    try:
        return classes[class_reference]
    except KeyError:
        raise NoSuchClassRegisteredError(f'No class was registered with reference: {class_reference}')


def _get_instance(class_reference: str, uid: int) -> Entity:
    pass


def _get_repr(item: Any) -> str:
    if isinstance(item, Entity):
        return f'get_instance({_get_class_reference(item.__class__)}, {object.__getattribute__(item, "__uid__")})'
    else:
        repr_ = repr(item)
        if repr_.strip().startswith('<'):
            raise UnsavableObjectError(f'object with rep: {repr_} cannot be saved with loss of data')
        return repr_


# sg_entity_after_delete = Signal()
# sg_entity_after_insert = Signal()
# sg_entity_after_update = Signal()
# sg_entity_before_delete = Signal()
# sg_entity_before_insert = Signal()
# sg_entity_before_update = Signal()
