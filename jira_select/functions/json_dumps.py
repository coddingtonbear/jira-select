import datetime
import json
from typing import Any, Optional

from pytz import UTC

from jira_select.plugin import BaseFunction
from .flatten_changelog import ChangelogEntry


ISO_FORMAT = "%Y-%m-%d %H:%M:%SZ"


class JiraSelectJsonEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return UTC.normalize(obj).strftime(ISO_FORMAT)
        elif isinstance(obj, ChangelogEntry):
            return {
                "author": obj.author,
                "created": UTC.normalize(obj.created).strftime(ISO_FORMAT),
                "field": obj.field,
                "fieldtype": obj.fieldtype,
                "fromValue": obj.fromValue,
                "fromString": obj.fromString,
                "toValue": obj.toValue,
                "toString": obj.toString,
            }
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


class Function(BaseFunction):
    """Dump an object as a JSON string.

    """
    def __call__(self, value: str, *args, **kwargs) -> Optional[str]:  # type: ignore[override]:
        return json.dumps(value, cls=JiraSelectJsonEncoder, *args, **kwargs)
