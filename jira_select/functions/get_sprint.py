from typing import Dict, Optional

from jira.resources import Sprint

from ..plugin import BaseFunction


class Function(BaseFunction):
    """ Returns a `jira.resources.Sprint` object for a given sprint ID string."""

    CACHE: Dict[int, str] = {}

    def get_sprint_details(self, id: int) -> Sprint:
        if id not in self.CACHE:
            self.CACHE[id] = self.jira.sprint(id)

        return self.CACHE[id]

    def __call__(self, id: Optional[int]) -> Optional[Sprint]:  # type: ignore[override]
        if id is None:
            return None

        return self.get_sprint_details(id)
