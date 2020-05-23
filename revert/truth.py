from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, List

from . import config
from .transaction import Transaction

__all__ = ['head', 'data', 'commit_parents', 'commit_messages', 'commit_children']

head: str = config.INIT_COMMIT
data: trie.Trie = None
commit_parents: DefaultDict[str, List[str]] = defaultdict(list)
commit_children: DefaultDict[str, List[str]] = defaultdict(list)
commit_messages: Dict[str, List[str]] = {}
directory: str
active_transactions: List[Transaction] = []

# noinspection PyUnresolvedReferences
from . import trie
