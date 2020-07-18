from typing import Any, Callable, Dict, Generator, List, Optional

from jira import JIRA, Issue
from rich.progress import Progress, TaskID

from .exceptions import UserError
from .plugin import get_installed_functions
from .types import QueryDefinition, SelectFieldDefinition
from .utils import (
    calculate_result_hash,
    get_field_data,
    get_row_dict,
    parse_order_by_definition,
    parse_select_definition,
)


class Result:
    def __init__(self, group_fields: List[str] = None):
        super().__init__()
        self._rows: List[Any] = []
        self._group_fields = group_fields if group_fields else []

    @property
    def rows(self):
        return self._rows

    @property
    def value_fields(self):
        return self._group_fields

    @property
    def scalar_fields(self):
        fields = set()

        for row in self._rows:
            fields |= set(get_row_dict(row))

        for row in self.value_fields:
            if row in fields:
                fields.remove(row)

        return fields

    def __hash__(self):
        return calculate_result_hash(self._rows[0], self.value_fields)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def add(self, record: Any):
        self._rows.append(record)

    def _grouped_as_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        first = get_row_dict(self._rows[0])

        for field in self.value_fields:
            result[field] = first[field]

        scalar_fields = self.scalar_fields

        for field in scalar_fields:
            # Exclude empty rows -- in SQL when you run an aggregation
            # function on a set of rows, NULL rows are skipped, so we
            # should probably do the same?
            result[field] = [
                get_row_dict(row)[field]
                for row in self._rows
                if get_row_dict(row).get(field) is not None
            ]

        return result

    def _single_as_dict(self) -> Dict[str, Any]:
        return get_row_dict(self._rows[0])

    def as_dict(self) -> Dict[str, Any]:
        if self._group_fields:
            return self._grouped_as_dict()
        return self._single_as_dict()

    def __getattr__(self, name):
        result = self.as_dict()

        if name not in result:
            raise AttributeError(name)

        return result[name]


class Query:
    def __init__(
        self, jira: JIRA, definition: QueryDefinition, progress_bar: bool = False
    ):
        self._definition: QueryDefinition = definition
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)
        self._progress_bar = progress_bar

    @property
    def progress_bar_enabled(self):
        return self._progress_bar

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

    def _get_issues(self, progress: Progress) -> Generator[Issue, None, None]:
        jql = self._get_jql()

        expand = self.definition.get("expand", [])

        start_at = 0
        max_results = 2 ** 32
        result_limit = self.definition.get("limit", 2 ** 32)

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("select", total=min(max_results, result_limit))

        while start_at < max_results:
            results = self.jira.search_issues(
                jql, startAt=start_at, expand=",".join(expand), fields="*all",
            )
            max_results = results.total
            for result in results:
                if task is not None:
                    progress.update(
                        task, advance=1, total=min(max_results, result_limit)
                    )

                yield result
                start_at += 1

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    return

    def _process_group_by(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        group_fields = self.definition.get("group_by", [])
        groups: Dict[int, Result] = {}

        if not group_fields:
            for row in iterator:
                result = Result()
                result.add(row)
                yield result
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("group_by", total=1)

        for row in iterator:
            row_hash = calculate_result_hash(row, group_fields)
            if row_hash not in groups:
                groups[row_hash] = Result(group_fields)

            groups[row_hash].add(row)

        if task is not None:
            progress.update(task, completed=0.5)

        for _, value in groups.items():
            yield value

        if task is not None:
            progress.update(task, completed=1)

    def _process_having(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        if not self.definition.get("having", []):
            yield from iterator
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("having", total=1)

        for row in iterator:
            include_row = True
            for having in self.definition["having"]:
                if not get_field_data(row, having, self._functions):
                    include_row = False
                    break

            if include_row:
                yield row

        if task is not None:
            progress.update(task, completed=1)

    def _process_order_by(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        if not self.definition.get("order_by", []):
            yield from iterator
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task(
                "order_by", total=len(self.definition["order_by"]) + 1
            )

        # First, materialize our list
        rows = list(iterator)

        # Now, order by each of the ordering expressions in reverse order
        for order_by in reversed(self.definition["order_by"]):
            rows = sorted(
                rows,
                key=lambda row: get_field_data(
                    row, parse_order_by_definition(order_by), self._functions
                ),
            )
            if task is not None:
                progress.update(task, advance=1)

        yield from rows

        if task is not None:
            progress.update(task, advance=1)

    def _get_iterator(self, progress: Progress) -> Generator[Any, None, None]:
        source = self.definition["from"]

        if source == "issues":
            iterator = self._get_issues
        else:
            raise NotImplementedError(f"No search for source {source} implemented.")

        yield from self._process_order_by(
            self._process_having(
                self._process_group_by(iterator(progress), progress), progress
            ),
            progress,
        )

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        with Progress() as progress:
            for row in self._get_iterator(progress):
                yield self._generate_row_dict(row)
