import datetime
from dataclasses import dataclass
from typing import Any
from typing import Iterator
from typing import List
from typing import Optional

from dateutil.parser import parse as parse_date

from ..exceptions import UserError
from ..plugin import BaseFunction


@dataclass
class ChangelogEntry:
    author: str = ""
    created: datetime.datetime = datetime.datetime.utcnow()
    id: int = -1
    field: str = ""
    fieldtype: str = ""
    fromValue: Optional[Any] = None
    fromString: Optional[str] = None
    toValue: Optional[Any] = None
    toString: Optional[str] = None


def flatten_changelog(changelog: Any) -> Iterator[ChangelogEntry]:
    for entry in changelog.histories:
        author = str(entry.author)
        created = parse_date(entry.created)
        id = int(entry.id)

        for item in entry.items:
            yield ChangelogEntry(
                author=author,
                created=created,
                id=id,
                field=item.field,
                fieldtype=item.fieldtype,
                fromValue=getattr(item, "from"),  # noqa
                fromString=item.fromString,
                toValue=getattr(item, "to"),  # noqa
                toString=item.toString,
            )


class Function(BaseFunction):
    """Returns a flattened list of changelog entries.


    Returns ``jira_select.functions.flatten_changelog.ChangelogEntry``
    entries for every changelog entry.
    """

    def __call__(self, changelog: Any) -> List[ChangelogEntry]:  # type: ignore[override]
        if changelog is None or not hasattr(changelog, "histories"):
            raise UserError(
                "No changelog was provided; did you use the ``expand`` "
                "option of ``changelog`` in your query?"
            )

        return list(flatten_changelog(changelog))
