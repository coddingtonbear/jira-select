from __future__ import annotations

import datetime
from typing import Any

import portion

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self, interval: portion.Interval, default=datetime.timedelta(seconds=0)
    ) -> portion.Interval:
        total: Any = default

        for subinterval in interval:
            result = subinterval.upper - subinterval.lower
            if total is None:
                total = result
            else:
                total += result

        return total
