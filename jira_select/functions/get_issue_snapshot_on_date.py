from __future__ import annotations

import copy
import datetime
from typing import Any
from typing import Iterator

from dateutil.parser import parse as parse_datetime
from dotmap import DotMap
from jira import JIRA
from jira.resources import Issue
from pytz import UTC

from jira_select.plugin import BaseFunction
from jira_select.plugin import get_installed_sources

from .flatten_changelog import flatten_changelog


class IssueSnapshotContainer(dict):
    _name_map: dict[str, Any] = {}

    def __init__(self, field_dict: dict[str, Any], name_map: dict[str, str]) -> None:
        self._name_map = name_map

        super().__init__(field_dict)

    def __getitem__(self, item: str) -> Any:
        if item not in self and item in self._name_map:
            return super().__getitem__(self._name_map[item])

        return super().__getitem__(item)

    def __setitem__(self, item: str, value: Any) -> None:
        if item not in self and item in self._name_map:
            return super().__setitem__(self._name_map[item], value)

        return super().__setitem__(item, value)


def get_customfield_to_name_mapping(jira: JIRA) -> dict[str, str]:
    schema = get_installed_sources()["issues"].get_schema(jira)
    return {row.description: row.id for row in schema if row.description}


def snapshot_iterator(issue: Issue, field_name_map: dict[str, str]) -> Iterator[DotMap]:
    non_snapshottable = [
        "changelog",
        "components",
        "comment",
        "expand",
        "parent",
        "raw",
        "self",
        "subtasks",
        "timetracking",
        "updated",
        "votes",
        "watches",
        "worklog",
    ]
    snapshot: dict[str, Any] = IssueSnapshotContainer(
        {
            k: (str(v) if v is not None else None)
            for k, v in issue.as_dict().items()
            if not callable(v) and k not in non_snapshottable
        },
        field_name_map,
    )
    snapshot_validity_end = datetime.datetime.utcnow().replace(tzinfo=UTC)

    flattened_changelog = sorted(
        flatten_changelog(issue.changelog),
        key=lambda row: row.created if row.created else datetime.date(1, 1, 1),
        reverse=True,
    )
    for entry in flattened_changelog:
        if entry.field in non_snapshottable:
            continue

        snapshot.update(
            {
                "validity_start": entry.created,
                "validity_end": snapshot_validity_end,
            }
        )

        yield DotMap(copy.deepcopy(snapshot))

        snapshot_validity_end = entry.created
        snapshot[entry.field] = (
            str(entry.fromString) if entry.fromString is not None else None
        )

    yield DotMap(copy.deepcopy(snapshot))


class Function(BaseFunction):
    """Returns an IssueSnapshot representing the Jira Issue's state on a particular date."""

    _field_name_map = None

    def get_customfield_to_name_mapping(self) -> dict[str, str]:
        if self._field_name_map is None:
            self._field_name_map = get_customfield_to_name_mapping(self.jira)

        return self._field_name_map

    def __call__(  # type: ignore[override]
        self, issue: Issue, date: datetime.datetime
    ) -> DotMap:
        last_snapshot: DotMap = DotMap({})

        if date > parse_datetime(issue.created):
            mapping = self.get_customfield_to_name_mapping()

            for snapshot in snapshot_iterator(issue, mapping):
                if parse_datetime(snapshot.created) < date:
                    return last_snapshot

                last_snapshot = snapshot

        return last_snapshot
