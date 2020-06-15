from __future__ import annotations

from typing import List, Optional, Any

from .trie import Trie

K = List[str]


class Transaction:
    __slots__ = ['old_values', 'new_values', 'messages', 'message']

    def __init__(self, message: str) -> None:
        self.message: str = message
        self.old_values: Trie = Trie()
        self.new_values: Trie = Trie()
        self.messages: List[str] = [message]

    def put(self, state: Trie, key: K, value: str) -> Optional[str]:
        old = state.put(key, value)
        self.new_values.put(key, value)
        if old is not None:
            self.old_values.put_if_not_present(key, old)
        return old

    def count_up_or_set(self, state: Trie, key: K) -> int:
        """returns new value"""
        old = state.count_up_or_set(key)
        new = 1 if old is None else old + 1
        self.new_values.put(key, str(new))
        if old is not None:
            self.old_values.put_if_not_present(key, str(old))
        return new

    def count_down_or_del(self, state: Trie, key: K) -> Optional[int]:
        """returns new value"""
        old = state.count_down_or_del(key)
        if old is None:
            return None
        new = old - 1
        if new == 0:
            self.new_values.discard(key)
        else:
            self.new_values.put(key, str(new))
        self.old_values.put_if_not_present(key, str(old))
        return new

    def discard(self, state: Trie, key: K) -> Optional[str]:
        old = state.discard(key)
        self.new_values.discard(key)
        if old is not None:
            self.old_values.put_if_not_present(key, old)
        return old

    def redo(self, state: Trie) -> None:
        for key in self.old_values.keys([]):
            state.discard(key)
        for key, value in self.new_values.items([]):
            state.put(key, value)

    def undo(self, state: Trie) -> None:
        for key in self.new_values.keys([]):
            state.discard(key)
        for key, value in self.old_values.items([]):
            state.put(key, value)

    def rollback(self, state: Trie) -> None:
        self.undo(state)
        self.old_values = Trie()
        self.new_values = Trie()
        self.messages = [self.message]

    def merge_into(self, parent: Transaction) -> None:
        for key, value in self.new_values.items([]):
            parent.new_values.put(key, value)
        for key, value in self.old_values.items([]):
            parent.old_values.put_if_not_present(key, value)
        parent.messages.extend(self.messages)

    def __bool__(self) -> bool:
        return self.old_values or self.new_values

    def to_json(self) -> Any:
        return {
            'old': self.old_values.to_json(),
            'new': self.new_values.to_json(),
            'messages': self.messages
        }

    @staticmethod
    def from_json(json: Any) -> Transaction:
        trans = Transaction(json['messages'][0])
        trans.messages = json['messages']
        trans.old_values = Trie.from_json(json['old'])
        trans.new_values = Trie.from_json(json['new'])
        return trans
