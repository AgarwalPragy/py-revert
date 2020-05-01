from datetime import datetime
from typing import Dict, Hashable, List, Set, Tuple, Union

PyON = Union[int, str, bool, float, None, datetime, Dict[Hashable, 'PyON'], Set[Hashable], List['PyON'], Tuple['PyON']]
