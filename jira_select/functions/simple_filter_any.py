from typing import Any
from typing import Dict
from typing import Iterable

from QueryableList import QueryableListMixed

from ..plugin import BaseFunction


class Function(BaseFunction):
    """Returns entries in an iterable matching a provided django-style query.

    Returned rows are required to match at least one of the provided query
    parameters.

    """

    def __call__(  # type: ignore[override]
        self, iterable: Iterable[Any], **query: Dict[str, Any]
    ) -> Iterable[Any]:
        queryable = QueryableListMixed(iterable)

        return queryable.filterOr(**query)
