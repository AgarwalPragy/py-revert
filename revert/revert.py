from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import Callable, ClassVar, DefaultDict, Dict, List, Optional, TypeVar
from uuid import uuid4

from intent import Intent

from . import config
from .exceptions import AmbiguousRedoError, InTransactionError, NoTransactionActiveError
from .trie import TrieDict

TCallable = TypeVar('TCallable', bound=Callable)

__all__ = ['connect', 'Transaction', 'undo', 'redo', 'checkout', 'intent_db_connected']

head: str = config.init_commit
data = TrieDict()
commit_parent = {}
commit_children: DefaultDict[str, List[str]] = defaultdict(list)
dir_: str
intent_db_connected: Intent[str] = Intent()
# todo: add more hooks
# todo: add global context manager to ensure data is saved in case of program termination
_deleted = object()


def connect(directory: str) -> None:
    global dir_, data, head, commit_parent
    dir_ = directory
    head_path = os.path.join(directory, config.head_file)
    if not os.path.exists(head_path):
        head = config.init_commit
        data = TrieDict()
    else:
        with open(head_path, 'r') as f:
            temp = json.loads(f.read())
            head = temp['head']
            data = TrieDict.from_json(temp['data'])
        with open(os.path.join(dir_, config.commit_parent_file), 'r') as f:
            temp = (line.split(',') for line in f.readlines())
            commit_parent = {line[0]: line[1] for line in temp}
            for commit, parent in commit_parent.items():
                commit_children[parent].append(commit)
    intent_db_connected.announce(directory)


def _save() -> None:
    with open(os.path.join(dir_, config.head_file), 'w') as f:
        f.write(json.dumps({
            'head': head,
            'data': data.to_json(),
        }, indent=4, sort_keys=True))


class Transaction:
    transaction_stack: ClassVar[List[Transaction]] = []
    messages: ClassVar[List[str]] = []

    dirty: TrieDict
    deleted: TrieDict
    message: str
    rollback_on_error: bool
    ignore_if_no_change: bool
    parent_transaction: Optional[Transaction] = None

    @staticmethod
    def current_transaction() -> Optional[Transaction]:
        return Transaction.transaction_stack[-1]

    @staticmethod
    def _commit_sub_transaction(parent_dirty: TrieDict, parent_deleted: TrieDict, dirty: TrieDict, deleted: TrieDict) -> None:
        for key, value in dirty.items():
            parent_dirty[key] = value
            parent_deleted.discard(key)
        for key, value in deleted.items():
            parent_deleted[key] = value
            parent_dirty.discard(key)

    @staticmethod
    def force_commit():
        global data, head
        all_dirty = TrieDict()
        all_deleted = TrieDict()
        messages = []
        for transaction in Transaction.transaction_stack:
            Transaction._commit_sub_transaction(all_dirty, all_deleted, transaction.dirty, transaction.deleted)
            messages.append(transaction.message)
        old = TrieDict({key: data[key] for key in all_dirty if key in data})
        for key in all_deleted:
            if key in data:
                old[key] = data[key]

        commit_id = f'{datetime.now()}_{uuid4()}'

        with open(os.path.join(dir_, f'{commit_id}.json'), 'w') as f:
            f.write(json.dumps({
                'parent': head,
                'old': old.to_json(),
                'new': all_dirty.to_json(),
                'messages': messages,
            }, indent=4, sort_keys=True))
        with open(os.path.join(dir_, config.commit_parent_file), 'a') as f:
            f.write(f'{commit_id},{head}\n')
        commit_parent[commit_id] = head
        data.update(all_dirty)
        for key in all_deleted:
            del data[key]
        head = commit_id
        _save()
        Transaction.transaction_stack = []
        Transaction.messages = []

    @staticmethod
    def count_up_or_set(key: str) -> None:
        op_value = Transaction.safe_get(key)
        if op_value is None:
            value = 0
        else:
            value = int(op_value)
        value += 1
        Transaction.set(key, str(value))

    @staticmethod
    def count_down_or_del(key: str) -> None:
        op_value = Transaction.get(key)
        if op_value is None:
            raise KeyError(key)
        value = int(op_value)
        value -= 1
        if value > 0:
            Transaction.set(key, str(value))
        else:
            Transaction.delete(key)

    @staticmethod
    def safe_get(key: str) -> Optional[str]:
        for transaction in Transaction.transaction_stack[::-1]:
            value = transaction.deleted.get(key)
            if value is not None:
                return None
            value = transaction.dirty.get(key)
            if value is not None:
                return value
        value = data.get(key)
        if value is None:
            return None
        else:
            return value

    @staticmethod
    def get(key: str) -> str:
        for transaction in Transaction.transaction_stack[::-1]:
            value = transaction.deleted.get(key)
            if value is not None:
                raise KeyError(key)
            value = transaction.dirty.get(key)
            if value is not None:
                return value
        value = data.get(key)
        if value is None:
            raise KeyError(key)
        else:
            return value

    @staticmethod
    def has(key: str) -> bool:
        for transaction in Transaction.transaction_stack[::-1]:
            if key in transaction.deleted:
                return False
            if key in transaction.dirty:
                return True
        return key in data

    @staticmethod
    def set(key: str, value: str) -> None:
        if not Transaction.transaction_stack:
            raise NoTransactionActiveError('Cannot change database values outside a transaction')
        tr = Transaction.transaction_stack[-1]
        tr.deleted.discard(key)
        tr.dirty[key] = value

    @staticmethod
    def discard(key: str) -> bool:
        if not Transaction.transaction_stack:
            raise NoTransactionActiveError('Cannot delete database values outside a transaction')
        if Transaction.has(key):
            Transaction.transaction_stack[-1].deleted[key] = ''
            Transaction.transaction_stack[-1].dirty.discard(key)
            return True
        else:
            return False

    @staticmethod
    def delete(key: str) -> None:
        if not Transaction.discard(key):
            raise KeyError(key)

    @classmethod
    def match_keys(cls, pattern: str) -> List[str]:
        keys = set(data.keys(pattern))
        transaction: Transaction
        for transaction in Transaction.transaction_stack:
            for key in transaction.dirty.keys(pattern):
                keys.add(key)
            for key in transaction.deleted.keys(pattern):
                keys.discard(key)
        return list(keys)

    @classmethod
    def match_items(cls, pattern: str) -> Dict[str, str]:
        items = {key: value for key, value in data.items(pattern)}
        transaction: Transaction
        for transaction in Transaction.transaction_stack:
            for key, value in transaction.dirty.items(pattern):
                items[key] = value
            for key in transaction.deleted.keys(pattern):
                if key in items:
                    del items[key]
        return items

    @classmethod
    def match_count(cls, pattern: str) -> int:
        if Transaction.transaction_stack:
            return len(Transaction.match_keys(pattern))
        return data.count(pattern)

    def __init__(self, message: str = '', rollback_on_error: bool = True, ignore_if_no_change: bool = False):
        self.message = message
        self.rollback_on_error = rollback_on_error
        self.ignore_if_no_change = ignore_if_no_change

    def __call__(self, func: TCallable) -> TCallable:
        @wraps(func)
        def wrapped(*args, **kwargs):
            with Transaction(message=self.message, rollback_on_error=self.rollback_on_error, ignore_if_no_change=self.ignore_if_no_change):
                func(*args, **kwargs)

        return wrapped  # type: ignore

    def __enter__(self):
        self.dirty = TrieDict()
        self.deleted = TrieDict()
        if Transaction.transaction_stack:
            self.parent_transaction = Transaction.transaction_stack[-1]
        Transaction.transaction_stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dirty or self.deleted or not self.ignore_if_no_change:
            Transaction.messages.append(self.message)
        parent = self.parent_transaction
        if parent is None:
            Transaction.force_commit()
        else:
            Transaction._commit_sub_transaction(parent.dirty, parent.deleted, self.dirty, self.deleted)
            Transaction.transaction_stack.pop()

    @staticmethod
    def rollback_current() -> None:
        if not Transaction.transaction_stack:
            return
        transaction = Transaction.transaction_stack[-1]
        transaction.dirty = TrieDict()
        transaction.deleted = TrieDict()

    @staticmethod
    def rollback_all() -> None:
        for transaction in Transaction.transaction_stack:
            transaction.dirty = TrieDict()
            transaction.deleted = TrieDict()
        Transaction.messages = []


def checkout(commit_id: str) -> None:
    global data, head
    if Transaction.transaction_stack:
        raise InTransactionError('Cannot checkout a commit while a transaction is active')
    history = [commit_id]
    parent = commit_id
    while parent != config.init_commit:
        history.append(parent)
        parent = commit_parent[parent]
    history_set = set(history)
    while head not in history_set:
        with open(os.path.join(dir_, f'{head}.json'), 'r') as f:
            temp = json.loads(f.read())
            old = temp['old']
            new = temp['new']
            for key in new:
                del data[key]
            for key, value in old.items():
                data[key] = value
        head = commit_parent[head]
    common_ancestor = head
    for commit_id in history[history.index(common_ancestor):]:
        with open(os.path.join(dir_, f'{commit_id}.json'), 'r') as f:
            temp = json.loads(f.read())
            old = temp['old']
            new = temp['new']
            for key in old:
                del data[key]
            for key, value in new.items():
                data[key] = value
        head = commit_id
    _save()


def undo() -> None:
    global data, head
    if Transaction.transaction_stack:
        raise InTransactionError('Cannot undo while a transaction is active')
    parent = commit_parent[head]
    with open(os.path.join(dir_, f'{head}.json'), 'r') as f:
        temp = json.loads(f.read())
        old = TrieDict.from_json(temp['old'])
        new = TrieDict.from_json(temp['new'])
        assert parent == temp['parent']
        for key in new:
            del data[key]
        for key, value in old.items():
            data[key] = value
    head = parent
    _save()


def redo() -> None:
    global data, head
    if Transaction.transaction_stack:
        raise InTransactionError('Cannot redo while a transaction is active')
    if len(commit_children[head]) == 0:
        return
    if len(commit_children[head]) > 1:
        raise AmbiguousRedoError(f'Ambiguous Redo: {head} has the following children: {commit_children[head]}')
    child = commit_children[head][0]
    with open(os.path.join(dir_, f'{child}.json'), 'r') as f:
        temp = json.loads(f.read())
        old = temp['old']
        new = temp['new']
        assert head == temp['parent']
        for key in old:
            del data[key]
        for key, value in new.items():
            data[key] = value
    head = child
    _save()
