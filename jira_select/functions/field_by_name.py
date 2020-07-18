from typing import Any, Optional, List

from ..plugin import BaseFunction
from ..query import Result


class Function(BaseFunction):
    FIELDS: Optional[List] = None

    def get_fields(self):
        if self.FIELDS is None:
            self.FIELDS = self.jira.fields()

        return self.FIELDS

    def process(self, row: Result, name: str) -> Optional[Any]:  # type: ignore[override]
        fields = self.get_fields()

        for field in fields:
            if field["name"] == name:
                return getattr(row, field["key"])

        return None
