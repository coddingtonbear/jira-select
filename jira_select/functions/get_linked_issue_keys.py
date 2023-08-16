from __future__ import annotations

from logging import getLogger

from jira_select.plugin import BaseFunction

logger = getLogger(__name__)


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self,
        issuelinks: list | None = None,
        link_type: str | None = None,
    ) -> list[str]:
        linked_keys: list[str] = []

        if issuelinks is None:
            raise ValueError(
                "issuelinks should be passed as the first parameter of 'get_linked_issue_keys'"
            )

        for link in (issuelink.raw for issuelink in issuelinks):
            if link["type"]["inward"] == link_type or link_type is None:
                if "inwardIssue" in link:
                    linked_keys.append(link["inwardIssue"]["key"])
            if link["type"]["outward"] == link_type or link_type is None:
                if "outwardIssue" in link:
                    linked_keys.append(link["outwardIssue"]["key"])

        return linked_keys
