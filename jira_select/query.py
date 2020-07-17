from typing import Any, Callable, Dict, Generator, List, Optional

from jira import JIRA, Issue

from .exceptions import UserError
from .plugin import get_installed_functions
from .types import QueryDefinition, SelectFieldDefinition
from .utils import get_field_data, parse_select_definition


class Query:
    def __init__(self, jira: JIRA, definition: QueryDefinition, emit_omissions=False):
        self._definition: QueryDefinition = definition
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)
        self._emit_omissions: bool = emit_omissions

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def definition(self) -> QueryDefinition:
        return self._definition

    def get_fields(self) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for field in self.definition["select"]:
            fields.append(parse_select_definition(field))

        return fields

    def _generate_row_dict(self, row: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.get_fields():
            result[field_defn["column"]] = get_field_data(
                row, field_defn["expression"], functions=self._functions
            )

        return result

    def _get_jql(self) -> str:
        where = self.definition.get("where")

        if where is None:
            return ""
        elif isinstance(where, List):
            return " AND ".join(self.definition["where"])

        raise UserError(f"Could not generate JQL from {where}.")

    def _get_issues(self) -> Generator[Issue, None, None]:
        jql = self._get_jql()

        expand = self.definition.get("expand", [])

        startAt = 0
        maxResults = float("inf")
        resultLimit = self.definition.get("limit", float("inf"))
        while startAt < maxResults:
            results = self.jira.search_issues(
                jql, startAt=startAt, expand=",".join(expand), fields="*all",
            )
            maxResults = results.total
            for result in results:
                yield result
                startAt += 1

                # Return early if our result limit has been reached
                if startAt >= resultLimit:
                    return

    def _get_issues_having(self) -> Generator[Optional[Issue], None, None]:
        for row in self._get_issues():
            include_row = True
            for having in self.definition.get("having", []):
                if not get_field_data(row, having, self._functions):
                    include_row = False
                    break

            if include_row:
                yield row
            elif self._emit_omissions:
                yield None

    def _get_iterator(self) -> Generator[Optional[Any], None, None]:
        source = self.definition["from"]
        source = self.definition["from"]

        if source == "issues":
            yield from self._get_issues_having()
        else:
            raise NotImplementedError(f"No search for source {source} implemented.")

    def count(self) -> int:
        jql = self._get_jql()

        resultLimit = self.definition.get("limit", float("inf"))

        return min(self.jira.search_issues(jql).total, resultLimit)

    def __iter__(self) -> Generator[Optional[Dict[str, Any]], None, None]:
        for row in self._get_iterator():
            if row is None:
                yield None
            else:
                yield self._generate_row_dict(row)
