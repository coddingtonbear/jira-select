import datetime
import re
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import cast

from dateutil.parser import parse as parse_date

from ..plugin import BaseFunction


@dataclass
class SprintInfo:
    id: int = -1
    name: str = ""
    state: str = ""
    goal: str = ""
    rapidViewId: Optional[int] = -1
    sequence: Optional[int] = -1
    startDate: Optional[datetime.datetime] = None
    endDate: Optional[datetime.datetime] = None
    completeDate: Optional[datetime.datetime] = None


class Function(BaseFunction):
    """Returns a `jira_select.functions.sprint_details.SprintInfo` object for a given sprint ID string."""

    def get_sprint_details(self, representation: str) -> Optional[SprintInfo]:
        # com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=ORC #11 3/9-3/23,goal=Code Complete 3/18,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436]
        field_converters: Dict[str, Callable] = {
            "id": int,
            "rapidViewId": int,
            "sequence": int,
            "startDate": parse_date,
            "endDate": parse_date,
            "completeDate": parse_date,
        }
        field_finder = re.compile(r"[^\[]+\[(?P<fields>[^\]]*)\]")

        field_data_match = field_finder.match(representation)

        if not field_data_match:
            return None

        raw_field_data = field_data_match.groupdict()["fields"]
        gathered: Dict[str, Optional[Any]] = {}

        if raw_field_data:
            for field_str in raw_field_data.split(","):
                k, v = field_str.split("=")

                if v == "<null>":
                    gathered[k] = None
                    continue

                gathered[k] = field_converters.get(k, lambda x: x)(v)

        return SprintInfo(
            id=cast(int, gathered.get("id", -1)),
            name=cast(str, gathered.get("name", "")),
            state=cast(str, gathered.get("state", "")),
            goal=cast(str, gathered.get("goal", "")),
            rapidViewId=cast(Optional[int], gathered.get("rapidViewId")),
            sequence=cast(Optional[int], gathered.get("sequence")),
            startDate=cast(Optional[datetime.datetime], gathered.get("startDate")),
            endDate=cast(Optional[datetime.datetime], gathered.get("endDate")),
            completeDate=cast(
                Optional[datetime.datetime], gathered.get("completeDate")
            ),
        )

    def __call__(self, sprint_blob: Optional[str]) -> Optional[SprintInfo]:  # type: ignore[override]
        if sprint_blob is None:
            return None

        return self.get_sprint_details(sprint_blob)
