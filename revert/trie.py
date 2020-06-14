from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from . import config

K = List[str]


def split(key: str) -> K:
    return [w for w in key.split(config.key_separator) if w]


class Trie:
    __slots__ = ['children', 'value', 'count']

    def __init__(self) -> None:
        self.children: Dict[str, Trie] = {}
        self.value: Optional[str] = None
        self.count: int = 0

    def __getitem__(self, key: K) -> Optional[str]:
        node = self
        for k in key:
            node = node.children.get(k, None)
            if node is None:
                return None
        return node.value

    def put(self, key: K, value: str) -> Optional[str]:
        node = self
        for k in key:
            child = node.children.get(k, None)
            if child is None:
                child = Trie()
                node.children[k] = child
            node = child
        oldvalue = node.value
        node.value = value
        if oldvalue is None:
            node.count += 1
            node = self
            for k in key:
                node.count += 1
                node = node.children[k]
        return oldvalue

    def put_if_not_present(self, key: K, value: str) -> None:
        node = self
        for k in key:
            child = node.children.get(k, None)
            if child is None:
                child = Trie()
                node.children[k] = child
            node = child
        if node.value is None:
            node.value = value
            node.count += 1
            node = self
            for k in key:
                node.count += 1
                node = node.children[k]

    def discard(self, key: K) -> Optional[str]:
        node = self
        for k in key:
            node = node.children.get(k, None)
            if node is None:
                return
        oldvalue = node.value
        if oldvalue is not None:
            node.value = None
            node.count -= 1
            node = self
            for k in key:
                node.count -= 1
                node = node.children[k]
        return oldvalue

    def __contains__(self, key: K) -> bool:
        node = self
        for k in key:
            node = node.children.get(k, None)
            if node is None:
                return False
        return node.value is not None

    def size(self, key: K) -> int:
        node = self
        for k in key:
            node = node.children.get(k, None)
            if node is None:
                return 0
        return node.count

    def __len__(self) -> int:
        return self.count

    def __bool__(self) -> bool:
        return self.count > 0

    def keys(self, prefix: K) -> Iterator[K]:
        if prefix:
            node = self
            for p in prefix:
                node = node.children.get(p, None)
                if node is None:
                    return
            for key in node.keys([]):
                yield prefix + key
        else:
            if self.value is not None:
                yield []
            for word, child in self.children.items():
                for key in child.keys([]):
                    yield [word] + key

    def items(self, prefix: K) -> Iterator[Tuple[K, str]]:
        if prefix:
            node = self
            for p in prefix:
                node = node.children.get(p, None)
                if node is None:
                    return
            for key, value in node.items([]):
                yield prefix + key, value
        else:
            if self.value is not None:
                yield [], self.value
            for word, child in self.children.items():
                for key, value in child.items([]):
                    yield [word] + key, value

    def to_json(self) -> Union[str, Dict[str, Any], Tuple[str, Dict[str, Any]]]:
        if not self.children:
            if self.value is not None:
                return self.value
            return {}
        children = {word: value.to_json() for word, value in self.children.items()}
        if self.value is not None:
            return self.value, children
        else:
            return children

    @staticmethod
    def from_json(data: Union[str, Dict[str, Any], Tuple[str, Dict[str, Any]]]) -> Trie:
        trie = Trie()
        if data == {}:
            return trie
        if isinstance(data, str):
            data = data.strip()
            trie.value = data
            trie.children = {}
        else:
            children: Dict[str, Any] = {}
            if isinstance(data, (list, tuple)):
                trie.value, children = data  # type: ignore
            elif isinstance(data, dict):
                trie.value = None
                children = data  # type: ignore
            for key, value in children.items():
                trie.children[key] = Trie.from_json(value)
        count = 0
        if trie.value is not None:
            count += 1
        for child in trie.children.values():
            count += len(child)
        trie.count = count
        return trie

    def clone(self) -> Trie:
        return Trie.from_json(self.to_json())

    def flatten(self) -> Dict[str, str]:
        return {config.key_separator.join(key): value for key, value in self.items([])}

    def __repr__(self) -> str:
        return str(self.to_json())

    def count_down_or_del(self, key: K) -> Optional[int]:

        pass

    def count_up_or_set(self, key: K) -> Optional[int]:
        pass
