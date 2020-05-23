from __future__ import annotations

from datetime import datetime
from typing import List, Tuple


def set_with_transaction(node: trie.Trie, key: List[str], value: str, trans: transaction.Transaction) -> Tuple[bool, bool]:
    ancestors = [node]
    for k in key:
        child = node.children.get(k, None)
        if child is None:
            child = trie.Trie()
            node.children[k] = child
        ancestors.append(child)
        node = child
    exists = node.value is not None
    changed = exists and node.value != value
    t_old_node = trie.navigate(key, trans.old_values)
    has_old = t_old_node is not None and t_old_node.value is not None
    if not exists and not has_old:
        trans.new_keys.set(key, '')
    else:
        t_new_node = trie.navigate(key, trans.new_keys)
        is_new = t_new_node is not None and t_new_node.value is not None
        if not exists and has_old and is_new:
            raise ValueError('wtf 1')
        elif exists and not has_old and not is_new:
            trans.old_values.set(key, node.value)
    updated_at = datetime.now()
    node.value = value
    for node in ancestors:
        if not exists:
            node.count += 1
            node.updated_at = updated_at
        if changed:
            node.updated_at = updated_at
    return exists, changed


def discard_with_transaction(node: trie.Trie, key: List[str], trans: transaction.Transaction) -> bool:
    ancestors = [node]
    for k in key:
        child = node.children.get(k, None)
        if child is None:
            return False
        ancestors.append(child)
        node = child
    if node.value is None:
        return False

    t_old_node = trie.navigate(key, trans.old_values)
    has_old = t_old_node is not None and t_old_node.value is not None
    if not has_old:
        t_new_node = trie.navigate(key, trans.new_keys)
        is_new = t_new_node is not None and t_new_node.value is not None
        if is_new:
            trans.new_keys.discard(key)
        else:
            trans.old_values.set(key, node.value)

    updated_at = datetime.now()
    node.value = None
    for node, k in zip(ancestors, key):
        child = node.children[k]
        node.updated_at = updated_at
        node.count -= 1
        if child.count == 1:
            del node.children[k]
            break
    return True


from . import trie
# noinspection PyUnresolvedReferences
from . import transaction
