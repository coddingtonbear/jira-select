import weakref
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List

from dotmap import DotMap
from jira import JIRA
from jira.resources import Issue
from simpleeval import NameNotDefined

from ..exceptions import QueryError
from ..plugin import BaseSource
from ..plugin import get_installed_functions
from ..types import SchemaRow
from ..utils import evaluate_expression


class Source(BaseSource):
    SCHEMA: List[SchemaRow] = [
        SchemaRow.parse_obj({"id": "key", "type": "str"}),
        SchemaRow.parse_obj({"id": "id", "type": "int"}),
    ]

    @classmethod
    def get_field_data(
        cls, row: Any, expression: str, functions: Dict[str, Callable]
    ) -> str:
        result = evaluate_expression(expression, row, functions=functions)
        if isinstance(result, str):
            return result
        return ""

    @classmethod
    def get_schema(cls, jira: JIRA) -> List[SchemaRow]:
        field_definitions: List[SchemaRow] = super().get_schema(jira)
        functions = get_installed_functions()

        for column in jira.fields():
            try:
                type = str(cls.get_field_data(DotMap(column), "schema.type", functions))
            except NameNotDefined:
                type = ""
            field_definitions.append(
                SchemaRow.parse_obj(
                    {
                        "id": str(cls.get_field_data(DotMap(column), "id", functions)),
                        "type": type,
                        "description": str(
                            cls.get_field_data(DotMap(column), "name", functions)
                        ),
                        "raw": DotMap(column),
                    }
                )
            )

        return field_definitions

    def _get_jql(self) -> str:
        if self.query.where and not isinstance(self.query.where, list):
            raise QueryError(
                "Issue queries 'where' should be a list of JQL expression strings."
            )

        assert isinstance(self.query.where, list)

        query = " AND ".join(f"({q})" for q in self.query.where)
        order_by_fields = ", ".join(self.query.order_by)

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def __iter__(self) -> Iterator[Dict]:
        start_at = 0
        max_results = 2**32
        result_limit = self.query.limit or 2**32

        jql = self._get_jql()

        self.update_progress(completed=0, total=1, visible=True)
        while start_at < min(max_results, result_limit):
            results = self.jira.search_issues(
                jql,
                startAt=start_at,
                expand=",".join(self.query.expand),
                fields="*all",
                maxResults=min(result_limit, 100),
            )

            max_results = results.total
            count = min([results.total, result_limit])
            self.update_count(count)

            for result in results:
                self.update_progress(advance=1, total=count, visible=True)

                yield result.raw

                start_at += 1

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    break

    def rehydrate(self, value: Dict) -> Issue:
        issue = Issue({}, None, value)

        if hasattr(issue, "changelog"):
            # the `changelog` contains only the _changes_ that have taken
            # place to the issue, but provides no way of undersatnding
            # the issue's original state.  Given that most uses of
            # the changelog in this tool depend on our being able to do
            # things like, e.g. understand the state of an issue at
            # a particular point in time, that's a problem because
            # the issue's initial state is not recorded in the changelog
            # and we'd need the issue object itself for calculating it.
            # Let's retain a weak reference to that original issue object
            # so we can do that when necessary.
            issue.changelog._issue = weakref.proxy(issue)

        return issue
