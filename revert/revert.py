from __future__ import annotations

import json
import os
from datetime import datetime
from functools import wraps
from typing import Callable, ClassVar, Dict, List, Optional, TypeVar
from uuid import uuid4

from exceptions import NoTransactionActiveError

TCallable = TypeVar('TCallable', bound=Callable)

__all__ = ['connect', 'Transaction', 'undo', 'redo', 'checkout']

head: str = 'init'
data: Dict[str, str] = {}
commit_dag = {}
dir_: str

_deleted = object()


def connect(directory: str) -> None:
    global dir_, data, head, commit_dag
    dir_ = directory
    head_path = os.path.join(directory, 'head.json')
    if not os.path.exists(head_path):
        head = 'init'
        data = {}
    else:
        with open(head_path, 'r') as f:
            temp = json.loads(f.read())
            head = temp['head']
            data = temp['data']
        with open(os.path.join(dir_, 'commit_dag.log'), 'r') as f:
            temp = (line.split(',') for line in f.readlines())
            commit_dag = {line[0]: line[1] for line in temp}


class Transaction:
    transaction_stack: ClassVar[List[Transaction]] = []
    messages: ClassVar[List[str]] = []

    dirty: Dict[str, str]
    message: str
    rollback_on_error: bool
    parent_transaction: Optional[Transaction] = None

    @staticmethod
    def current_transaction() -> Optional[Transaction]:
        return Transaction.transaction_stack[-1]

    @staticmethod
    def force_commit():
        global data, head
        dirty = {}
        messages = []
        for transaction in Transaction.transaction_stack:
            dirty.update(transaction.dirty)
            messages.append(transaction.message)
        commit_id = f'{datetime.now()}_{uuid4()}'
        with open(os.path.join(dir_, f'{commit_id}.json'), 'w') as f:
            f.write(json.dumps({
                'parent': head,
                'old': {key: data[key] for key in dirty if key in data},
                'new': dirty,
            }, indent=4, sort_keys=True))
        with open(os.path.join(dir_, 'commit_dag.log'), 'a') as f:
            f.write(f'{head},{commit_id}\n')
        data.update(dirty)
        head = commit_id
        with open(os.path.join(dir_, 'head.json'), 'w') as f:
            f.write(json.dumps({
                'head': head,
                'data': data,
            }, indent=4, sort_keys=True))
        Transaction.transaction_stack = []
        Transaction.messages = []

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> str:
        for transaction in Transaction.transaction_stack[::-1]:
            value = transaction.dirty.get(key, None)
            if value is not None:
                return value
        if default is not None:
            return data.get(key, default)
        else:
            return data[key]

    @staticmethod
    def has(key: str) -> bool:
        for transaction in Transaction.transaction_stack[::-1]:
            if key in transaction.dirty:
                return True
        return key in data

    @staticmethod
    def set(key: str, value: str) -> None:
        if not Transaction.transaction_stack:
            raise NoTransactionActiveError('Cannot change database values outside a transaction')
        Transaction.transaction_stack[-1].dirty[key] = value

    @staticmethod
    def delete(key: str, ignore_if_not_present: bool = False) -> None:
        pass

    @classmethod
    def match(cls, pattern: str) -> List[str]:
        items = data.copy()
        for transaction in Transaction.transaction_stack:
            items.update(transaction.dirty)
        return [key for key in items.keys() if key.startswith(pattern)]

    @classmethod
    def match_count(cls, pattern: str) -> int:
        items = data.copy()
        for transaction in Transaction.transaction_stack:
            items.update(transaction.dirty)
        return sum(1 for key in items.keys() if key.startswith(pattern))

    def __init__(self, message: str = '', rollback_on_error: bool = True):
        self.message = message
        self.rollback_on_error = rollback_on_error

    def __call__(self, func: TCallable) -> TCallable:
        @wraps
        def wrapped(*args, **kwargs):
            with Transaction(message=self.message, rollback_on_error=self.rollback_on_error) as t:
                func(*args, **kwargs)

        return wrapped

    def __enter__(self):
        self.dirty = {}
        if Transaction.transaction_stack:
            self.parent_transaction = Transaction.transaction_stack[-1]
        Transaction.transaction_stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dirty:
            Transaction.messages.append(self.message)
        parent = self.parent_transaction
        if parent is None:
            Transaction.force_commit()
        else:
            parent.dirty.update(self.dirty)
            Transaction.transaction_stack.pop()

    @staticmethod
    def rollback_current() -> None:
        if not Transaction.transaction_stack:
            return
        transaction = Transaction.transaction_stack[-1]
        transaction.dirty = {}

    @staticmethod
    def rollback_all() -> None:
        for transaction in Transaction.transaction_stack:
            transaction.dirty = {}
        Transaction.messages = []


def checkout(commit_id: str) -> None:
    pass


def undo() -> None:
    pass


def redo() -> None:
    pass
