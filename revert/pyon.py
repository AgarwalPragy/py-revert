from datetime import datetime
from typing import Union, Dict, Set, Hashable, List, Tuple

PyON = Union[int, str, bool, float, None, datetime, Dict[Hashable, 'PyON'], Set[Hashable], List['PyON'], Tuple['PyON']]
