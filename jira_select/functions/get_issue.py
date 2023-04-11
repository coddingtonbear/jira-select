from __future__ import annotations

from typing import Optional

import jira.resources

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    """Fetch a Jira issue by name."""

    def __call__(  # type: ignore[override]
        self,
        ticket_number: str,
    ) -> Optional[jira.resources.Issue]:
        if ticket_number:
            return self.jira.issue(ticket_number)

        return None
