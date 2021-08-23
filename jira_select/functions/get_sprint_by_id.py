from typing import Dict
from typing import Optional

from jira.resources import Sprint

from ..plugin import BaseFunction


class Function(BaseFunction):
    """Returns a `jira.resources.Sprint` object for a given sprint ID string."""

    CACHE: Dict[int, Sprint] = {}

    def get_sprint_details(self, id: int) -> Sprint:
        if id not in self.CACHE:
            sprint = self.jira.sprint(id)
            self.CACHE[id] = Sprint(
                {"agile_rest_path": self.jira._options["agile_rest_path"]},
                None,
                sprint.raw,
            )

        return self.CACHE[id]

    def __call__(self, id: Optional[int]) -> Optional[Sprint]:  # type: ignore[override]
        if id is None:
            return None

        return self.get_sprint_details(id)
