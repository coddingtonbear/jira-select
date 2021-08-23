from typing import Any
from typing import Optional

from dateutil.parser import parse as parse_datetime
from pytz import UTC

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    """Parse a date string into a datetime object.

     If no timezone is specified, UTC is assumed.

    This relies on `python-dateutil`; there are many additional options available
    that you can find documented `here <https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse>`_.

    """

    def __call__(self, date_str, *args, **kwargs) -> Optional[Any]:  # type: ignore[override]
        datetime = parse_datetime(date_str, *args, **kwargs)

        if not datetime.tzinfo:
            datetime = UTC.localize(datetime)

        return datetime
