import csv
import re
from typing import Any, Dict, Generator, cast, List, IO

from jira import JIRA, Issue

from .exceptions import UserError
from .types import JQLIssueQuery, ListIssueQuery, QueryDefinition, Field


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

    def _generate_fieldnames(self) -> List[str]:
        fields = []

        for field in self.definition["select"]:
            fields.append(self._get_field_display(field))

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

    def _get_field_display(self, field: Field) -> str:
        if isinstance(field, dict):
            return field["display"]

        assert isinstance(field, str)

        matched = self.FIELD_DISPLAY_DEFN_RE.match(field)
        if matched:
            return matched.groupdict()["display"]

        return field

    def _get_field_path(self, field: Field) -> str:
        if isinstance(field, dict):
            return field["field"]

        assert isinstance(field, str)

        matched = self.FIELD_DISPLAY_DEFN_RE.match(field)
        if matched:
            return matched.groupdict()["field"]

        return field

    def _generate_row_dict(self, row: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.definition["select"]:
            field_display = self._get_field_display(field_defn)
            field_path = self._get_field_path(field_defn)

            result[field_display] = self._get_field_data(row, field_path)

        return result

    def _get_issues(self) -> Generator[Issue, None, None]:
        if isinstance(self.definition["where"], dict):
            where = cast(JQLIssueQuery, self.definition["where"])
            if "jql" not in where:
                raise UserError("Expected field 'jql' in query 'where' clause.")
            jql = where["jql"]
        else:
            where = cast(ListIssueQuery, self.definition["where"])
            jql = " AND ".join(where)

        expand = self.definition.get("expand", [])

        startAt = 0
        maxResults = float("inf")
        while startAt < maxResults:
            results = self.jira.search_issues(jql, startAt=startAt)
            maxResults = results.total
            for result in results:
                yield self.jira.issue(result.key, expand=",".join(expand))
                startAt += 1

    def __iter__(self) -> Generator[Any, None, None]:
        source = self.definition["from"]

        if source == "issues":
            yield from self._get_issues()
        else:
            raise NotImplementedError(f"No search for source {source} implemented.")

    def write_csv(self, stream: IO[str]):
        out = csv.DictWriter(stream, fieldnames=self._generate_fieldnames())
        out.writeheader()

        for row in self:
            out.writerow(self._generate_row_dict(row))
