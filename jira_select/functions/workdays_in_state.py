import datetime
from typing import Any

from pytz import UTC, timezone
from dateutil.tz import tzlocal
from dateutil.parser import parse as parse_datetime

from jira_select.plugin import BaseFunction
from .flatten_changelog import ChangelogEntry, Function as FlattenChangelog


class Function(BaseFunction):
    """Count the fractional number of work days an issue was in a given state."""

    def __call__(
        self,
        changelog: Any,
        state: str,
        start_hour: int | None = 9,
        end_hour: int | None = 17,
        timezone_name: str | None = None,
        work_days: list[int] = [1, 2, 3, 4, 5],
        min_date: datetime.date = datetime.date(1, 1, 1),
        max_date: datetime.date = datetime.date(9999, 1, 1),
    ):
        try:
            tz = timezone(timezone_name) if timezone_name is not None else tzlocal()

            flattened_changelog = sorted(
                FlattenChangelog(self.jira)(changelog),
                key=lambda row: row.created,
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
        except:
            import traceback, sys

            traceback.print_exc()
            sys.exit(1)

        return total_time.total_seconds() / (60 * 60 * (end_hour - start_hour))
