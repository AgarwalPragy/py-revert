from __future__ import annotations

import json
import os
from contextlib import contextmanager
from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Iterator

from intent import Intent

from . import config, db_state
from .exceptions import AmbiguousRedoError, InTransactionError, NoTransactionActiveError, AmbiguousUndoError
from .transaction import Transaction
from .trie import Trie, split

__all__ = ['connect', 'undo', 'redo', 'checkout', 'get_commit_dag',
           'safe_get', 'get', 'put', 'delete', 'discard', 'has',
           'count_up_or_set', 'count_down_or_del', 'match_count', 'match_keys', 'match_items',
           'transaction',
           'intent_db_connected']

# todo: add more hooks
intent_db_connected: Intent[str] = Intent()


def get_commit_dag() -> Tuple[str, Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]:
    return (db_state.head, deepcopy(db_state.commit_parents), deepcopy(db_state.commit_children),
            deepcopy(db_state.commit_messages))


def connect(directory: str) -> None:
    print('connecting to db at', directory)
    db_state.directory = directory
    head_path = os.path.join(db_state.directory, f'{config.head_file}_{config.device_name}')
    state = Trie()
    db_state.state = state
    db_state.head = config.init_commit
    commits_path = os.path.join(directory, config.commit_parents_file)
    if os.path.exists(commits_path):
        with open(commits_path, 'r') as f:
            for line in f.readlines():
                commit, parents, messages = json.loads(line)
                db_state.commit_parents[commit] = parents
                db_state.commit_messages[commit] = messages
                for parent in parents:
                    db_state.commit_children[parent].append(commit)
        if os.path.exists(head_path):
            with open(head_path, 'r') as f:
                expected_head = f.read().strip()
                checkout(expected_head)
        else:
            db_state.head = config.init_commit
    intent_db_connected.announce(directory)


def _update_head():
    head_path = os.path.join(db_state.directory, f'{config.head_file}_{config.device_name}')
    with open(head_path, 'w') as f:
        f.write(db_state.head)


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
    for key in db_state.state.keys(split(prefix)):
        yield config.key_separator.join(key)


def match_items(prefix: str) -> Iterator[Tuple[str, str]]:
    for key, value in db_state.state.items(split(prefix)):
        yield config.key_separator.join(key), value


@contextmanager
def transaction(message: str):
    db_state.active_transactions.append(Transaction(message))
    yield
    trans = db_state.active_transactions.pop()
    if db_state.active_transactions:
        trans.merge_into(db_state.active_transactions[-1])
    else:
        db_state.state.update_hash(trans.new_values)
        db_state.state.update_hash(trans.old_values)
        commit_id = db_state.state.hash
        if commit_id == db_state.head:
            print('Transaction did not change anything! Skipping commit.')
            return
        if commit_id not in db_state.commit_parents:
            print('creating commit', commit_id)
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
            db_state.commit_children[db_state.head].append(commit_id)
        else:
            # transaction wasn't empty, but ended up recreating an existing commit!
            # todo: create a pseudo-child?
            pass
        db_state.head = commit_id
        _update_head()


def checkout(commit_id: str) -> None:
    if commit_id == db_state.head:
        return
    if db_state.active_transactions:
        raise InTransactionError('Cannot checkout a commit while a transaction is active')
    print('checking out', commit_id)
    commit_id = commit_id.strip()
    history = [commit_id]
    parent = commit_id
    commit_parents = db_state.commit_parents
    while parent != config.init_commit:
        if len(commit_parents[parent]) > 1:
            raise NotImplementedError('Cannot work with multiple parents at present')
        parent = commit_parents[parent][0]
        history.append(parent)
    history = history[::-1]
    history_set = set(history)
    common_ancestor = db_state.head
    changed_keys = Trie()
    while common_ancestor not in history_set:
        with open(os.path.join(db_state.directory, f'{common_ancestor}.json'), 'r') as f:
            trans = Transaction.from_json(json.loads(f.read()))
            trans.undo(db_state.state)
            for key in trans.new_values.keys([]):
                changed_keys.put(key, '')
            for key in trans.old_values.keys([]):
                changed_keys.put(key, '')
        if len(commit_parents[common_ancestor]) > 1:
            raise NotImplementedError('Cannot work with multiple parents at present')
        common_ancestor = commit_parents[common_ancestor][0]
    for commit_id in history[history.index(common_ancestor):]:
        if commit_id == config.init_commit:
            continue
        with open(os.path.join(db_state.directory, f'{commit_id}.json'), 'r') as f:
            trans = Transaction.from_json(json.loads(f.read()))
            trans.redo(db_state.state)
            for key in trans.new_values.keys([]):
                changed_keys.put(key, '')
            for key in trans.old_values.keys([]):
                changed_keys.put(key, '')
    db_state.state.update_hash(changed_keys)
    if commit_id != config.init_commit and db_state.state.hash != commit_id:
        print(f'expected hash does not match hash of actual data!\nexpected: {commit_id}\nactual: {db_state.state.hash}')
        import sys
        sys.exit(1)
    db_state.head = commit_id
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
# todo: have multiple ordered parents of each commit.
#       Last parent will be the highest priority and will be the conflict resolution parent
# https://www.cs.tufts.edu/~nr/cs257/archive/david-roundy/theory-patches-2009.pdf
# https://arxiv.org/abs/1311.3903
