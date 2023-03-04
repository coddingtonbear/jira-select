from typing import Any
from typing import Optional

from dateutil.parser import parse as parse_datetime

from jira_select.plugin import BaseFunction


class Function(BaseFunction):
    """Parse a date string into a date object.

    This relies on `python-dateutil`; there are many additional options available
    that you can find documented `here <https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse>`_.

    """

    def __call__(self, date_str, *args, **kwargs) -> Optional[Any]:  # type: ignore[override]
        datetime = parse_datetime(date_str, *args, **kwargs)

        return datetime.date()
