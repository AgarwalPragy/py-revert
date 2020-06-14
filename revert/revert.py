from __future__ import annotations

import json
import os
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, TypeVar, Iterator
from uuid import uuid4

from intent import Intent

from . import config, db_state
from .exceptions import AmbiguousRedoError, InTransactionError, NoTransactionActiveError, AmbiguousUndoError
from .transaction import Transaction
from .trie import Trie, split

TCallable = TypeVar('TCallable', bound=Callable)

__all__ = ['connect', 'undo', 'redo', 'checkout', 'get_commit_dag',
           'get',
           'put',
           'discard',
           'count_up_or_set',
           'count_down_or_del',
           'has',
           'match_count',
           'match_keys',
           'match_items',
           'intent_db_connected']

# todo: add more hooks
intent_db_connected: Intent[str] = Intent()


def get_commit_dag() -> Tuple[str, Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]:
    return (db_state.head, deepcopy(db_state.commit_parents), deepcopy(db_state.commit_children),
            deepcopy(db_state.commit_messages))


def connect(directory: str) -> None:
    print('connecting to db at', directory)
    db_state.directory = directory
    head_path = os.path.join(db_state.directory, config.head_file)
    state = Trie()
    db_state.state = state
    if os.path.exists(head_path):
        with open(os.path.join(directory, config.commit_parents_file), 'r') as f:
            for line in f.readlines():
                commit, parents, messages = json.loads(line)
            db_state.commit_parents[commit] = parents
            db_state.commit_messages[commit] = messages
            for parent in parents:
                db_state.commit_children[parent].append(commit)
        with open(head_path, 'r') as f:
            expected_head = f.read().strip()
        checkout(expected_head)
    intent_db_connected.announce(directory)


def rollback_current_transaction() -> None:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('No transaction available to rollback')
    db_state.active_transactions[-1].rollback(db_state.state)


def rollback_all_transactions() -> None:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('No transaction available to rollback')
    for trans in reversed(db_state.active_transactions):
        trans.rollback(db_state.state)


def safe_get(key: str) -> Optional[str]:
    return db_state.state[split(key)]


def get(key: str) -> str:
    value = db_state.state[split(key)]
    if value is None:
        raise KeyError(key)
    return value


def put(key: str, value: str) -> None:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('Cannot change database values outside a transaction')
    return db_state.active_transactions[-1].put(db_state.state, split(key), value)


def count_up_or_set(key: str) -> int:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('Cannot change database values outside a transaction')
    return db_state.active_transactions[-1].count_up_or_set(db_state.state, split(key))


def count_down_or_del(key: str) -> int:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('Cannot change database values outside a transaction')
    return db_state.active_transactions[-1].count_down_or_del(db_state.state, split(key))


def discard(key: str) -> None:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('Cannot delete database values outside a transaction')
    return db_state.active_transactions[-1].discard(db_state.state, split(key))


def delete(key: str) -> None:
    if not db_state.active_transactions:
        raise NoTransactionActiveError('Cannot delete database values outside a transaction')
    value = db_state.active_transactions[-1].discard(db_state.state, split(key))
    if value is None:
        raise KeyError(key)


def has(key: str) -> bool:
    return split(key) in db_state.state


def match_count(prefix: str) -> int:
    return db_state.state.size(split(prefix))


def match_keys(prefix: str) -> Iterator[str]:
    for key in db_state.state.keys(prefix):
        yield config.key_separator.join(key)


def match_items(prefix: str) -> Iterator[Tuple[str, str]]:
    for key, value in db_state.state.items(prefix):
        yield config.key_separator.join(key), value


@contextmanager
def transaction(message: str):
    db_state.active_transactions.append(Transaction(message))
    yield
    trans = db_state.active_transactions.pop()
    if db_state.active_transactions:
        trans.merge_into(db_state.active_transactions[-1])
    else:
        commit_id = f'{datetime.now()}_{uuid4()}'
        with open(os.path.join(db_state.directory, f'{commit_id}.json'), 'w') as f:
            f.write(json.dumps({
                'parents': [db_state.head],
                'messages': trans.messages,
                'old': trans.old_values.to_json(),
                'new': trans.new_values.to_json(),
            }))
        with open(os.path.join(db_state.directory, config.commit_parents_file), 'a') as f:
            f.write(json.dumps([commit_id, [db_state.head], trans.messages]) + '\n')
        db_state.commit_parents[commit_id].append(db_state.head)
        db_state.head = commit_id


def checkout(commit_id: str) -> None:
    if db_state.active_transactions:
        raise InTransactionError('Cannot checkout a commit while a transaction is active')
    commit_id = commit_id.strip()
    history = [commit_id]
    parent = commit_id
    while parent != config.init_commit:
        history.append(parent)
        parent = commit_parent[parent]
    history.append(config.init_commit)
    history = history[::-1]
    history_set = set(history)
    common_ancestor = head
    while common_ancestor not in history_set:
        with open(os.path.join(dir_, f'{common_ancestor}.json'), 'r') as f:
            temp = json.loads(f.read())
            old = temp['old']
            new = temp['new']
            for key in new:
                if key in data:
                    del data[key]
            for key, value in old.items():
                data[key] = value
        common_ancestor = commit_parent[common_ancestor]
    for commit_id in history[history.index(common_ancestor):]:
        if commit_id == config.init_commit:
            continue
        with open(os.path.join(dir_, f'{commit_id}.json'), 'r') as f:
            temp = json.loads(f.read())
            old = Trie.from_json(temp['old'])
            new = Trie.from_json(temp['new'])
            for key in old:
                if key in data:
                    del data[key]
            for key, value in new.items():
                data[key] = value
        head = commit_id
    _update_head()


def undo() -> None:
    if db_state.active_transactions:
        raise InTransactionError('Cannot undo while a transaction is active')
    parents = db_state.commit_parents[db_state.head]
    if len(parents) == 0:
        return
    if len(parents) > 1:
        raise AmbiguousUndoError(f'Ambiguous Undo: {db_state.head} has the following parents: {parents}')
    checkout(parents[0])


def redo() -> None:
    if db_state.active_transactions:
        raise InTransactionError('Cannot redo while a transaction is active')
    children = db_state.commit_children[db_state.head]
    if len(children) == 0:
        return
    if len(children) > 1:
        raise AmbiguousRedoError(f'Ambiguous Redo: {db_state.head} has the following children: {children}')
    checkout(children[0])

# todo: add merge commit functionality with conflict resolution
# todo: have multiple ordered parents of each commit. Last parent will be the higest priority and will be the conflict resolution parent
