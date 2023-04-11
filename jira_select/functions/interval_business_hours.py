from __future__ import annotations

import datetime
from typing import Iterable

import portion
from dateutil.tz import tzlocal
from pytz import timezone

from jira_select.plugin import BaseFunction


def get_business_hours_intervals(
    start: datetime.date,
    end: datetime.date,
    start_hour: int = 9,
    end_hour: int = 17,
    timezone_name: str | None = None,
    work_days: Iterable[int] = (1, 2, 3, 4, 5),
) -> portion.Interval:
    business_hours = portion.empty()

    tz = timezone(timezone_name) if timezone_name is not None else tzlocal()
    cursor = start
    while cursor < end:
        if int(cursor.strftime("%w")) in work_days:
            min_day_date = datetime.datetime(
                year=cursor.year,
                month=cursor.month,
                day=cursor.day,
                hour=start_hour,
            ).replace(tzinfo=tz)
            max_day_date = datetime.datetime(
                year=cursor.year,
                month=cursor.month,
                day=cursor.day,
                hour=end_hour,
            ).replace(tzinfo=tz)

            business_hours |= portion.closed(min_day_date, max_day_date)

        cursor += datetime.timedelta(days=1)

    return business_hours


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self,
        min_date: datetime.date | None = None,
        max_date: datetime.date | None = None,
        start_hour: int = 9,
        end_hour: int = 17,
        timezone_name: str | None = None,
        work_days: Iterable[int] = (1, 2, 3, 4, 5),
    ) -> portion.Interval:
        if min_date is None:
            min_date = datetime.datetime.now().date() - datetime.timedelta(days=365)
        if max_date is None:
            max_date = datetime.datetime.now().date() + datetime.timedelta(days=1)

        return get_business_hours_intervals(
            min_date,
            max_date,
            start_hour,
            end_hour,
            timezone_name,
            work_days,
        )
