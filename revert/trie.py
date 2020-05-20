from __future__ import annotations

from typing import Any, Dict, Generator, Iterator, List, Mapping, Optional, Tuple, Union

from . import config


def split_first(key: str) -> Tuple[str, str]:
    i = 0
    for i, c in enumerate(key):
        if c != config.key_separator:
            break
    index = key.find(config.key_separator, i)
    if index == -1:
        return key[i:], ''
    return key[i:index], key[index + 1:]


class TrieDict:
    _children: Dict[str, TrieDict]
    _value: Optional[str] = None
    _count: int = 0

    def __init__(self, data=Union[Dict[str, str], List[Tuple[str, str]]]) -> None:
        self._children = {}
        if isinstance(data, dict):
            for key, value in data.items():
                self[key] = value
        elif isinstance(data, list):
            for key, value in data:
                self[key] = value

    def __getitem__(self, key: str) -> str:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: str) -> None:
        self._set(key, value)

    def __delitem__(self, key: str) -> None:
        exists = self.discard(key)
        if not exists:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return self.keys()

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        k, key = split_first(key)
        if not k:
            return self._value is not None
        return k in self._children and key in self._children[k]

    def __len__(self) -> int:
        return self._count

    def __bool__(self) -> bool:
        return self._count > 0

    def get(self, key: str) -> Optional[str]:
        k, key = split_first(key)
        if not k:
            return self._value
        if k not in self._children:
            self._children[k] = TrieDict()
        return self._children[k].get(key)

    def _set(self, key: str, value: str) -> bool:
        k, key = split_first(key)
        if not k:
            exists = self._value is not None
            self._value = value
            if not exists:
                self._count += 1
            return exists
        if k not in self._children:
            self._children[k] = TrieDict()
        exists = self._children[k]._set(key, value)
        if not exists:
            self._count += 1
        return exists

    def discard(self, key: str) -> bool:
        k, key = split_first(key)
        if not k:
            exists = self._value is not None
            self._value = None
            if exists:
                self._count -= 1
            return exists
        if k not in self._children:
            self._children[k] = TrieDict()
        exists = self._children[k].discard(key)
        if not self._children[k]:
            del self._children[k]
        if exists:
            self._count -= 1
        return exists

    def keys(self, prefix: str = '') -> Generator[str, None, None]:
        p, prefix = split_first(prefix)
        if not p:
            if self._value is not None:
                yield ''
            for key, item in self._children.items():
                for k in item:
                    if k:
                        yield key + config.key_separator + k
                    else:
                        yield key
        else:
            if p not in self._children:
                return
            for key in self._children[p].keys(prefix):
                yield p + config.key_separator + key

    def items(self, prefix: str = '') -> Generator[Tuple[str, str], None, None]:
        p, prefix = split_first(prefix)
        if not p:
            if self._value is not None:
                yield '', self._value
            for prefix, child in self._children.items():
                for key, value in child.items():
                    if key:
                        yield prefix + config.key_separator + key, value
                    else:
                        yield prefix, value
        else:
            if p not in self._children:
                return
            for key, value in self._children[p].items(prefix):
                yield p + config.key_separator + key, value

    def count(self, prefix: str = '') -> int:
        p, prefix = split_first(prefix)
        if not p:
            return self._count
        else:
            if p not in self._children:
                return 0
            return self._children[p].count(prefix)

    def update(self, other: Mapping[str, str]) -> None:
        for key, value in other.items():
            self[key] = value

    def to_json(self) -> Union[str, Dict[str, Any], Tuple[str, Dict[str, Any]]]:
        if not self._children:
            if self._value is not None:
                return self._value
            return '{}'
        children = {key: value.to_json() for key, value in self._children.items()}
        if self._value is not None:
            return self._value, children
        else:
            return children

    @staticmethod
    def from_json(data: Union[str, Dict[str, Any], Tuple[str, Dict[str, Any]]]) -> TrieDict:
        trie = TrieDict()
        if isinstance(data, str):
            data = data.strip()
            if data == '{}':
                return trie
            trie._value = data
            trie._children = {}
        else:
            children: Dict[str, Any] = {}
            if isinstance(data, (list, tuple)):
                trie._value, children = data  # type: ignore
            elif isinstance(data, dict):
                trie._value = None
                children = data  # type: ignore
            for key, value in children.items():
                trie._children[key] = TrieDict.from_json(value)
        count = 0
        if trie._value is not None:
            count += 1
        for child in trie._children.values():
            count += len(child)
        trie._count = count
        return trie

    def clone(self) -> TrieDict:
        return TrieDict.from_json(self.to_json())

    def flatten(self) -> Dict[str, str]:
        return {key: value for key, value in self.items()}

    def __repr__(self) -> str:
        return str(self.to_json())
