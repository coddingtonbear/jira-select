import datetime
from typing import Any
from typing import List
from typing import Optional

from dateutil.tz import tzlocal
from pytz import UTC
from pytz import timezone

from jira_select.plugin import BaseFunction

from .flatten_changelog import Function as FlattenChangelog


class Function(BaseFunction):
    """Count the fractional number of work days an issue was in a given state."""

    def __call__(  # type: ignore[override]
        self,
        changelog: Any,
        state: str,
        start_hour: Optional[int] = 9,
        end_hour: Optional[int] = 17,
        timezone_name: Optional[str] = None,
        work_days: List[int] = [1, 2, 3, 4, 5],
        min_date: datetime.date = datetime.date(1, 1, 1),
        max_date: datetime.date = datetime.date(9999, 1, 1),
    ):
        tz = timezone(timezone_name) if timezone_name is not None else tzlocal()

        flattened_changelog = sorted(
            FlattenChangelog(self.jira)(changelog),
            key=lambda row: row.created if row.created else datetime.date(1, 1, 1),
        )

        total_time = datetime.timedelta()

        cursor = min_date
        while cursor < max_date:
            if int(cursor.strftime("%w")) in work_days:
                min_day_date = datetime.datetime(
                    year=cursor.year,
                    month=cursor.month,
                    day=cursor.day,
                    hour=start_hour if start_hour is not None else 0,
                ).replace(tzinfo=tz)
                max_day_date = (
                    datetime.datetime(
                        year=cursor.year,
                        month=cursor.month,
                        day=cursor.day,
                        hour=end_hour,
                    ).replace(tzinfo=tz)
                    if end_hour is not None
                    else min_day_date + datetime.timedelta(days=1)
                )

                state_start: datetime.datetime | None = None
                for entry in flattened_changelog:
                    if entry.field != "status":
                        continue

                    if state_start is not None and entry.created:
                        valid_state_start = max(state_start, min_day_date)
                        valid_state_end = min(entry.created, max_day_date)
                        if valid_state_start < valid_state_end:
                            total_time += valid_state_end - valid_state_start
                        state_start = None
                    if entry.toString == state:
                        state_start = entry.created

                if state_start is not None:
                    valid_state_start = max(state_start, min_day_date)
                    valid_state_end = min(
                        max_day_date,
                        UTC.localize(datetime.datetime.utcnow()),
                    )
                    if valid_state_start < valid_state_end:
                        total_time += valid_state_end - valid_state_start

            cursor += datetime.timedelta(days=1)

        divisor = 1
        if end_hour is not None and start_hour is not None:
            divisor = 60 * 60 * (end_hour - start_hour)

        return total_time.total_seconds() / divisor
