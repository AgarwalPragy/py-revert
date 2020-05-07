from __future__ import annotations

from typing import Any, Dict, Generator, Iterator, List, Mapping, Optional, Tuple, Union

separator = '/'


def split_first(key: str) -> Tuple[str, str]:
    index = key.find(separator)
    if index == -1:
        return key, ''
    else:
        return key[:index], key[index + 1:]


class TrieDict(Mapping[str, str]):
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
        if not key:
            return self._value is not None
        k, key = split_first(key)
        return k in self._children and key in self._children[k]

    def __len__(self) -> int:
        return self._count

    def __bool__(self) -> bool:
        return self._count > 0

    def get(self, key: str) -> Optional[str]:
        if not key:
            return self._value
        k, key = split_first(key)
        if k not in self._children:
            self._children[k] = TrieDict()
        return self._children[k].get(key)

    def _set(self, key: str, value: str) -> bool:
        if not key:
            exists = self._value is not None
            self._value = value
            if not exists:
                self._count += 1
            return exists
        k, key = split_first(key)
        if k not in self._children:
            self._children[k] = TrieDict()
        exists = self._children[k]._set(key, value)
        if not exists:
            self._count += 1
        return exists

    def discard(self, key: str) -> bool:
        if not key:
            exists = self._value is not None
            self._value = None
            if exists:
                self._count -= 1
            return exists
        k, key = split_first(key)
        if k not in self._children:
            self._children[k] = TrieDict()
        exists = self._children[k].discard(key)
        if not self._children[k]:
            del self._children[k]
        if exists:
            self._count -= 1
        return exists

    def keys(self, prefix: str = '') -> Generator[str, None, None]:
        if not prefix:
            if self._value is not None:
                yield ''
            for key, item in self._children.items():
                for k in item:
                    if k:
                        yield key + separator + k
                    else:
                        yield key
        else:
            p, prefix = split_first(prefix)
            if p not in self._children:
                return
            for key in self._children[p].keys(prefix):
                yield p + separator + key

    def items(self, prefix: str = '') -> Generator[Tuple[str, str], None, None]:
        if not prefix:
            if self._value is not None:
                yield '', self._value
            for prefix, child in self._children.items():
                for key, value in child.items():
                    if key:
                        yield prefix + separator + key, value
                    else:
                        yield prefix, value
        else:
            p, prefix = split_first(prefix)
            if p not in self._children:
                return
            for key, value in self._children[p].items(prefix):
                yield p + separator + key, value

    def count(self, prefix: str = '') -> int:
        if not prefix:
            return self._count
        else:
            p, prefix = split_first(prefix)
            if p not in self._children:
                return 0
            return self._children[p].count(prefix)

    def update(self, other: Mapping[str, str]) -> None:
        for key, value in other.items():
            self[key] = value

    def to_json(self) -> Union[str, Tuple[int, Dict[str, Any]], Tuple[str, int, Dict[str, Any]]]:
        if not self._children:
            if self._value is not None:
                return self._value
            return '{}'
        children = {key: value.to_json() for key, value in self._children.items()}
        if self._value is not None:
            return self._value, self._count, children
        else:
            return self._count, children

    @staticmethod
    def from_json(data: Union[str, Tuple[int, Dict[str, Any]], Tuple[str, int, Dict[str, Any]]]) -> TrieDict:
        trie = TrieDict()
        if data == '{}':
            return trie
        if isinstance(data, str):
            trie._value = data
            trie._count = 1
            trie._children = {}
        else:
            if len(data) == 3:
                trie._value, trie._count, children = data
            else:
                trie._value = None
                trie._count, children = data
            for key, value in children.items():
                trie._children[key] = TrieDict.from_json(value)
        return trie

    def copy(self):
        return TrieDict.from_json(self.to_json())

    def __repr__(self):
        return str(self.to_json())

#
# if __name__ == '__main__':
#     t = TrieDict()
#     print(t.to_json())
#     print(t.copy().to_json())
#     t['hello'] = 'x'
#     print(t.to_json())
#     print(t.copy().to_json())
#     t['hello/world'] = 'x'
#     print(t.to_json())
#     print(t.copy().to_json())
#     t['buffalo/python'] = 'x'
#     print(t.to_json())
#     print(t.copy().to_json())
#     del t['hello/world']
#     print(t.to_json())
#     print(t.copy().to_json())
#     del t['buffalo/python']
#     print(t.to_json())
#     print(t.copy().to_json())
#     del t['hello']
#     print(t.to_json())
#     print(t.copy().to_json())
