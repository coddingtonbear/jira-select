import re
from typing import Dict, Optional

from jira.resources import Sprint

from ..plugin import BaseFunction


class Function(BaseFunction):
    """ Returns a `jira.resources.Sprint` object for a given sprint ID string."""

    CACHE: Dict[int, str] = {}

    def get_sprint_details(self, representation: str) -> Sprint:
        # com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=ORC #11 3/9-3/23,goal=Code Complete 3/18,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436
        sprint_field_matcher = re.compile(
            r"com.atlassian.greenhopper.service.sprint.Sprint@.*id=(?P<id>\d+)[^\d].*"  # noqa
        )
        match = sprint_field_matcher.match(representation)
        if not match:
            return None

        id = int(match.groupdict()["id"])

        if id not in self.CACHE:
            self.CACHE[id] = self.jira.sprint(id)

        return self.CACHE[id]

    def __call__(self, sprint_id: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if sprint_id is None:
            return None

        return self.get_sprint_details(sprint_id)
