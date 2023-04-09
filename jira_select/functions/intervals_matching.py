from __future__ import annotations

from typing import Any

import portion
from jira.resources import Issue

from jira_select.plugin import BaseFunction

from .get_issue_snapshot_on_date import get_customfield_to_name_mapping
from .get_issue_snapshot_on_date import snapshot_iterator
from .simple_filter import simple_filter


class Function(BaseFunction):
    _field_name_map = None

    def get_customfield_to_name_mapping(self) -> dict[str, str]:
        if self._field_name_map is None:
            self._field_name_map = get_customfield_to_name_mapping(self.jira)

        return self._field_name_map

    def __call__(  # type: ignore[override]
        self, issue: Issue, **filter_params: dict[str, Any]
    ) -> portion.Interval:
        field_name_map = self.get_customfield_to_name_mapping()
        interval = portion.empty()

        matching_snapshots = simple_filter(
            list(snapshot_iterator(issue, field_name_map)), **filter_params
        )

        for snapshot in matching_snapshots:
            interval |= portion.closed(snapshot.validity_start, snapshot.validity_end)

        return interval
