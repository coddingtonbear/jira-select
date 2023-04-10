from __future__ import annotations

from typing import Any

import portion

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self, interval: portion.Interval
    ) -> portion.Interval:
        total: Any = None

        for subinterval in interval:
            result = subinterval.upper - subinterval.lower
            if total is None:
                total = result
            else:
                total += result

        return total
