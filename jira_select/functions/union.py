from __future__ import annotations

import operator
from functools import reduce
from typing import Iterable
from typing import TypeVar

from jira_select.plugin import BaseFunction

X = TypeVar("X")


class Function(BaseFunction):
    def __call__(self, iterable: Iterable[X]) -> X:  # type: ignore[override]
        return reduce(operator.or_, iterable)
