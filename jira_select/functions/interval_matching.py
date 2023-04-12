from __future__ import annotations

from typing import Any

import portion
from jira.resources import Issue

from jira_select.plugin import BaseFunction

from .get_issue_snapshot_on_date import snapshot_iterator
from .simple_filter import simple_filter


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self, issue: Issue, **filter_params: dict[str, Any]
    ) -> portion.Interval:
        interval = portion.empty()

        matching_snapshots = simple_filter(
            list(
                snapshot_iterator(
                    issue, self.executor.field_name_map if self.executor else {}
                )
            ),
            **filter_params,
        )

        for snapshot in matching_snapshots:
            interval |= portion.closed(snapshot.validity_start, snapshot.validity_end)

        return interval
