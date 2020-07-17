from typing import Any, Callable, Dict, Generator, List

from jira import JIRA, Issue

from .exceptions import UserError
from .plugin import get_installed_functions
from .types import QueryDefinition, SelectFieldDefinition
from .utils import get_field_data, parse_select_definition


class Query:
    def __init__(self, jira: JIRA, definition: QueryDefinition):
        self._definition: QueryDefinition = definition
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)

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
