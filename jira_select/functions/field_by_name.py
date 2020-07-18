from typing import Any, Optional, List

from ..plugin import BaseFunction
from ..query import Result


class Function(BaseFunction):
    """ Returns value in row for field having the specified human-readable name.

    Note that jira-select provides the row under the variable name `_`.

    E.g::

        select
            - field_by_name(_, "Story Points")
        from: issues

    """

    FIELDS: Optional[List] = None

    def get_fields(self):
        if self.FIELDS is None:
            self.FIELDS = self.jira.fields()

        return self.FIELDS

    def __call__(self, row: Result, name: str) -> Optional[Any]:  # type: ignore[override]
        fields = self.get_fields()

        for field in fields:
            if field["name"] == name:
                return getattr(row, field["key"])

        return None