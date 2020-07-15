import re
from typing import Any, Dict, Generator, cast, List

from jira import JIRA, Issue

from .exceptions import UserError
from .types import (
    JQLIssueQuery,
    ListIssueQuery,
    QueryDefinition,
    SelectFieldDefinition,
)


class Query:
    FIELD_DISPLAY_DEFN_RE = re.compile(r'^(?P<field>[\w.]+) as "(?P<display>.*)"$')

    def __init__(self, jira: JIRA, definition: QueryDefinition):
        self._definition: QueryDefinition = definition
        self._jira: JIRA = jira

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def definition(self) -> QueryDefinition:
        return self._definition

    def get_fields(self) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for field in self.definition["select"]:
            if isinstance(field, str):
                as_match = self.FIELD_DISPLAY_DEFN_RE.match(field)
                display = field
                if as_match:
                    match_dict = as_match.groupdict()
                    field = match_dict["field"]
                    display = match_dict["display"]

                fields.append({"field": field, "display": display})
            else:
                fields.append(field)

        return fields

    def _get_field_data(self, row: Any, field: str) -> Any:
        if field == "key":
            return row.key

        dotpath = field.split(".")
        cursor = row.fields

        for part in dotpath:
            try:
                cursor = getattr(cursor, part)
            except (AttributeError, TypeError):
                return None

        return cursor

    def _generate_row_dict(self, row: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.get_fields():
            result[field_defn["display"]] = self._get_field_data(
                row, field_defn["field"]
            )

        return result

    def _get_jql(self) -> str:
        if isinstance(self.definition["where"], dict):
            where = cast(JQLIssueQuery, self.definition["where"])
            if "jql" not in where:
                raise UserError("Expected field 'jql' in query 'where' clause.")
            jql = where["jql"]
        else:
            where = cast(ListIssueQuery, self.definition["where"])
            jql = " AND ".join(where)

        return jql

    def _get_issues(self) -> Generator[Issue, None, None]:
        jql = self._get_jql()

        expand = self.definition.get("expand", [])

        startAt = 0
        maxResults = float("inf")
        while startAt < maxResults:
            results = self.jira.search_issues(jql, startAt=startAt)
            maxResults = results.total
            for result in results:
                yield self.jira.issue(result.key, expand=",".join(expand))
                startAt += 1

    def _get_iterator(self) -> Generator[Any, None, None]:
        source = self.definition["from"]
        source = self.definition["from"]

        if source == "issues":
            yield from self._get_issues()
        else:
            raise NotImplementedError(f"No search for source {source} implemented.")

    def count(self) -> int:
        jql = self._get_jql()

        return self.jira.search_issues(jql).total

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        for row in self._get_iterator():
            yield self._generate_row_dict(row)
