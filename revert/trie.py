from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple

from . import config

__all__ = ['safe_split', 'navigate', 'Trie']


def safe_split(key: str) -> List[str]:
    words = [w.replace(config.KEY_SEPARATOR, '') for w in key.split(config.KEY_SEPARATOR)]
    return [w for w in words if w]


def navigate(key: List[str], node: Trie) -> Optional[Trie]:
    for k in key:
        node = node.children.get(k, None)
        if node is None:
            break
    return node


class Trie:
    children: Dict[str, Trie]
    value: Optional[str]
    created_at: datetime
    updated_at: datetime
    count: int

    def __init__(self) -> None:
        self.value = None
        now = datetime.now()
        self.created_at = now
        self.updated_at = now
        self.count = 0
        self.children = {}

    def __getitem__(self, key: List[str]) -> Optional[str]:
        node = navigate(key, self)
        return None if node is None else node.value

    def __contains__(self, key: List[str]) -> bool:
        node = navigate(key, self)
        return node is not None and node.value is not None

    def __len__(self) -> int:
        return self.count

    def __bool__(self) -> bool:
        return self.count > 0

    def match_count(self, prefix: List[str]) -> int:
        node = navigate(prefix, self)
        return 0 if node is None else node.count

    def set(self, key: List[str], value: str) -> Tuple[bool, bool]:
        node = self
        ancestors = [self]
        for k in key:
            child = node.children.get(k, None)
            if child is None:
                child = Trie()
                node.children[k] = child
            ancestors.append(child)
            node = child
        exists = node.value is not None
        changed = exists and node.value != value
        updated_at = datetime.now()
        node.value = value
        for node in ancestors:
            if not exists:
                node.count += 1
                node.updated_at = updated_at
            if changed:
                node.updated_at = updated_at
        return exists, changed

    def discard(self, key: List[str]) -> bool:
        node = self
        ancestors = [self]
        for k in key:
            child = node.children.get(k, None)
            if child is None:
                return False
            ancestors.append(child)
            node = child
        if node.value is None:
            return False
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

    def __iter__(self) -> Iterator[str]:
        return self.keys([])

    def keys(self, prefix: List[str]) -> Generator[str, None, None]:
        node = navigate(prefix, self)
        if node is None:
            return
        if node.value is not None:
            yield config.KEY_SEPARATOR.join(prefix)
        for key, child in node.children.items():
            prefix.append(key)
            for k in child.keys([]):
                if k:
                    prefix.append(k)
                yield config.KEY_SEPARATOR.join(prefix)
                if k:
                    prefix.pop()
            prefix.pop()

    def items(self, prefix: List[str]) -> Generator[Tuple[str, str], None, None]:
        node = navigate(prefix, self)
        if node is None:
            return
        if node.value is not None:
            yield config.KEY_SEPARATOR.join(prefix), node.value
        for key, child in node.children.items():
            prefix.append(key)
            for k, v in child.items([]):
                if k:
                    prefix.append(k)
                yield config.KEY_SEPARATOR.join(prefix), v
                if k:
                    prefix.pop()
            prefix.pop()

    def to_json(self) -> Any:
        children = {key: value.to_json() for key, value in self.children.items()}
        return [self.value, str(self.created_at), str(self.updated_at), children]

    @staticmethod
    def from_json(data: Any) -> Trie:
        trie = Trie()
        trie.value, created, updated, children = data
        trie.created_at = datetime.fromisoformat(created)
        trie.updated_at = datetime.fromisoformat(updated)
        trie.children = {}
        for key, value in list(children.items()):
            trie.children[key] = Trie.from_json(value)
        count = 0
        if trie.value is not None:
            count += 1
        for child in trie.children.values():
            count += len(child)
        trie.count = count
        return trie

    def flatten(self) -> Dict[str, str]:
        return {key: value for key, value in self.items([])}

    def __repr__(self) -> str:
        return f'Trie.from_json({json.dumps(self.to_json())})'
