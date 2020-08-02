from typing import Dict, List, Iterator

from jira import JIRA
from jira.resources import Issue

from ..plugin import BaseSource
from ..types import SelectFieldDefinition


class Source(BaseSource):
    FIELDS: List[SelectFieldDefinition] = [
        {"expression": "key", "column": "key",},
        {"expression": "id", "column": "id",},
    ]

    @classmethod
    def get_all_fields(cls, jira: JIRA) -> List[SelectFieldDefinition]:
        field_definitions: List[SelectFieldDefinition] = super().get_all_fields(jira)

        for field in jira.fields():
            definition: SelectFieldDefinition = {
                "expression": field["id"],
                "column": field["id"],
            }
            field_definitions.append(definition)

        return field_definitions

    def _get_jql(self) -> str:
        query = " AND ".join(f"({q})" for q in self.query.where)
        order_by_fields = ", ".join(self.query.order_by)

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def __iter__(self) -> Iterator[Dict]:
        start_at = 0
        max_results = 2 ** 32
        result_limit = self.query.limit or 2 ** 32

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
        return Issue({}, None, value)
