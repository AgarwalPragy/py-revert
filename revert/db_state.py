from collections import defaultdict
from typing import List, Dict, DefaultDict

from . import config
from .transaction import Transaction
from .trie import Trie

__all__ = []

directory: str = ''

head: str = config.init_commit

state = Trie()
active_transactions: List[Transaction] = []

commit_parents: Dict[str, List[str]] = defaultdict(list)
commit_children: DefaultDict[str, List[str]] = defaultdict(list)
commit_messages: Dict[str, List[str]] = {}
