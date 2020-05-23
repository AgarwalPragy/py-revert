from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable, Optional, Tuple, TypeVar

from .exceptions import NoTransactionActiveError

__all__ = ['get', 'has', 'match_keys', 'match_count', 'match_items',
           'discard', 'set', 'count_up_or_set', 'count_down_or_del',
           'Transaction']

from .trie_transaction import set_with_transaction, discard_with_transaction

TCallable = TypeVar('TCallable', bound=Callable)


def get(key: str) -> Optional[str]:
    return truth.data[trie.safe_split(key)]


def has(key: str) -> bool:
    return trie.safe_split(key) in truth.data


def match_count(key: str = '') -> int:
    return truth.data.match_count(trie.safe_split(key))


def match_keys(prefix: str = '') -> Iterable[str]:
    return truth.data.keys(trie.safe_split(prefix))


def match_items(prefix: str = '') -> Iterable[Tuple[str, str]]:
    return truth.data.items(trie.safe_split(prefix))


def set(key: str, value: str) -> Tuple[bool, bool]:
    if not truth.active_transactions:
        raise NoTransactionActiveError('Cannot change database values outside a transaction')
    return set_with_transaction(truth.data, trie.safe_split(key), value, truth.active_transactions[-1])


def discard(key: str) -> bool:
    if not truth.active_transactions:
        raise NoTransactionActiveError('Cannot delete database values outside a transaction')
    return discard_with_transaction(truth.data, trie.safe_split(key), truth.active_transactions[-1])


def count_up_or_set(key: str) -> int:
    if not truth.active_transactions:
        raise NoTransactionActiveError('Cannot delete database values outside a transaction')
    k = trie.safe_split(key)
    value = truth.data[k]
    if value is None:
        value = '0'
    value = int(value) + 1
    set_with_transaction(truth.data, k, str(value), truth.active_transactions[-1])
    return value
    # todo: optimize by supporting below function
    # return truth.data.count_up_or_set_with_transaction(trie.safe_split(key), truth.active_transactions[-1])


def count_down_or_del(key: str) -> int:
    if not truth.active_transactions:
        raise NoTransactionActiveError('Cannot delete database values outside a transaction')
    k = trie.safe_split(key)
    value = truth.data[k]
    if value is None:
        return 0
    value = int(value) - 1
    if value == 0:
        discard_with_transaction(truth.data, k, truth.active_transactions[-1])
    else:
        set_with_transaction(truth.data, k, str(value), truth.active_transactions[-1])
    return value
    # todo: optimize by supporting below function
    # return truth.data.count_down_or_del_with_transaction(trie.safe_split(key), truth.active_transactions[-1])


class Transaction:
    old_values: trie.Trie
    new_keys: trie.Trie
    message: str

    def __init__(self, message: str = ''):
        self.message = message
        self.old_values = trie.Trie()
        self.new_keys = trie.Trie()

    def __call__(self, func: TCallable) -> TCallable:
        @wraps(func)
        def wrapped(*args, **kwargs):
            with Transaction(message=self.message):
                func(*args, **kwargs)

        return wrapped  # type: ignore

    # def __enter__(self):
    #     truth.active_transactions.append(self)
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     if self.old_values or self.new_keys:
    #         Transaction.messages.append(self.message)
    #     if parent is None:
    #         Transaction.force_commit()
    #     else:
    #         Transaction._commit_sub_transaction(parent.dirty, parent.deleted, self.dirty, self.deleted)
    #         Transaction.transaction_stack.pop()
    #
    # @staticmethod
    # def rollback_current() -> None:
    #     if not Transaction.transaction_stack:
    #         return
    #     transaction = Transaction.transaction_stack[-1]
    #     transaction.dirty = Trie()
    #     transaction.deleted = Trie()


from . import truth
from . import trie
