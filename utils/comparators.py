from collections.abc import Callable
from datetime import datetime
import operator

from enums.sort_order import SortOrder

DateComparator = Callable[[datetime, datetime], bool]

SORT_COMPARATORS: dict[SortOrder, DateComparator] = {
    SortOrder.ASC: operator.le,
    SortOrder.DESC: operator.ge,
}
