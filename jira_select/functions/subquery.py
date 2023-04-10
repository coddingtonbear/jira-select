from __future__ import annotations

from logging import getLogger
from typing import Any

from jira_select.plugin import BaseFunction

from ..exceptions import JiraSelectError
from ..exceptions import QueryError
from ..query import Executor

logger = getLogger(__name__)


class Function(BaseFunction):
    def __call__(  # type: ignore[override]
        self, subquery_name: str, **params: dict[str, Any]
    ) -> list[Any]:
        params = params if params is not None else {}
        results: list[Any] = []

        if not self.query:
            raise JiraSelectError("Parent query unexpectedly unavailable to subquery.")

        try:
            query_definition = self.query.subqueries[subquery_name]
        except KeyError as exc:
            raise QueryError(
                f"Subquery '{subquery_name}' does not exist in query definition."
            ) from exc

        # Unless explicitly set, subqueries use the same
        # caching duration as their parent query
        if query_definition.cache is None and self.query.cache:
            query_definition.cache = self.query.cache

        query = Executor(
            self.jira,
            query_definition,
            progress_bar=False,
            parameters=params,
        )
        for row in query:
            row_values = list(row.values())
            if len(query_definition.select) == 1:
                results.append(row_values[0])
            else:
                results.append(row_values)

        return results
