import jira.resources

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    """Fetch a Jira issue by name."""

    def __call__(  # type: ignore[override]
        self,
        ticket_number: str,
    ) -> jira.resources.Issue | None:
        if ticket_number:
            return self.jira.issue(ticket_number)

        return None
