from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import total_ordering
from typing import Any, Callable, Dict, Generator, List, Optional, cast

from jira import JIRA, Issue
from rich.progress import Progress, TaskID

from .plugin import get_installed_functions
from .types import ExpressionList, QueryDefinition, SelectFieldDefinition, Expression
from .utils import (
    calculate_result_hash,
    clean_query_definition,
    expression_includes_group_by,
    get_field_data,
    get_row_dict,
    parse_sort_by_definition,
    parse_select_definition,
)


@total_ordering
class NullAcceptableSort:
    def __init__(self, value: Any):
        self._value = value

    def __le__(self, other):
        if other._value is None:
            return True
        if self._value is None:
            return False

        return self._value < other._value

    def __eq__(self, other):
        if self._value is other._value:
            return True

        return self._value == other._value

    def __str__(self):
        return str(self._value)


class Result(metaclass=ABCMeta):
    def __getattr__(self, name):
        result = self.as_dict()

        if name not in result:
            raise AttributeError(name)

        return result[name]

    @abstractmethod
    def as_dict(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def single(self) -> SingleResult:
        ...

    def evaluate_expression(
        self,
        expression: Expression,
        group_by: ExpressionList = None,
        functions: Dict[str, Callable] = None,
    ):
        if group_by is None:
            group_by = []

        row_source = self

        # Force returning a single value if the expression under
        # evaluation is one we're grouping on
        if expression_includes_group_by(expression, group_by):
            row_source = self.single()

        return get_field_data(row_source, expression, functions)


class SingleResult(Result):
    def __init__(self, row: Any):
        self._row = row

    def as_dict(self) -> Dict[str, Any]:
        return get_row_dict(self._row)

    def single(self) -> SingleResult:
        return self


class GroupedResult(Result):
    def __init__(
        self, rows: List[SingleResult] = None,
    ):
        super().__init__()
        self._rows: List[SingleResult] = rows if rows is not None else []

    @property
    def rows(self):
        return self._rows

    @property
    def all_fields(self):
        fields = set()

        for row in self._rows:
            fields |= set(row.as_dict())

        return fields

    def add(self, record: SingleResult):
        self._rows.append(record)

    def single(self) -> SingleResult:
        return self.rows[0]

    def as_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field in self.all_fields:
            # Exclude empty rows -- in SQL when you run an aggregation
            # function on a set of rows, NULL rows are skipped, so we
            # should probably do the same?
            result[field] = [
                row.as_dict()[field]
                for row in self._rows
                if row.as_dict().get(field) is not None
            ]

        return result


class Query:
    def __init__(
        self, jira: JIRA, definition: QueryDefinition, progress_bar: bool = False
    ):
        self._definition: QueryDefinition = clean_query_definition(definition)
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)
        self._progress_bar = progress_bar

        # Set a high ceiling at the start so the progressbar does not
        # start "full"
        self._query_count = 2 ** 32
        self._group_by_count = 2 ** 32
        self._having_count = 2 ** 32
        self._sort_by_count = 2 ** 32

    @property
    def progress_bar_enabled(self):
        return self._progress_bar

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def definition(self) -> QueryDefinition:
        return self._definition

    @property
    def functions(self) -> Dict[str, Callable]:
        return self._functions

    def get_fields(self) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for field in self.definition["select"]:
            fields.append(parse_select_definition(field))

        return fields

    def _get_jql(self) -> str:
        query = " AND ".join(self.definition.get("where", []))
        order_by_fields = ", ".join(self.definition.get("order_by", []))

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def _get_issues(self, progress: Progress) -> Generator[SingleResult, None, None]:
        jql = self._get_jql()

        expand = self.definition.get("expand", [])

        start_at = 0
        max_results = 2 ** 32
        result_limit = self.definition.get("limit", 2 ** 32)

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("query", total=self.query_count)

        while start_at < max_results:
            results = self.jira.search_issues(
                jql,
                startAt=start_at,
                expand=",".join(expand),
                fields="*all",
                maxResults=min(result_limit, 100),
            )
            max_results = results.total
            self._query_count = min(results.total, result_limit)
            for result in results:
                result = cast(Issue, result)
                if task is not None:
                    progress.update(task, advance=1, total=self.query_count)

                start_at += 1
                yield SingleResult(result)

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    return

    @property
    def query_count(self):
        return self._query_count

    def _process_group_by(
        self, iterator: Generator[SingleResult, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        group_fields = self.definition.get("group_by", [])
        groups: Dict[int, GroupedResult] = {}
        self._group_by_count = 0

        if not group_fields:
            for row in iterator:
                self._group_by_count = self.query_count
                yield row
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("group_by", total=self.query_count)

        for row in iterator:
            if task is not None:
                progress.update(task, total=self.query_count)

            row_hash = calculate_result_hash(row, group_fields, self.functions,)
            if row_hash not in groups:
                self._group_by_count += 1
                groups[row_hash] = GroupedResult()

            groups[row_hash].add(row)

            if task is not None:
                progress.update(task, advance=1)

        for _, value in groups.items():
            yield value

    @property
    def group_by_count(self):
        return self._group_by_count

    def _process_having(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        self._having_count = 0
        if not self.definition.get("having", []):
            for row in iterator:
                yield row
                self._having_count += 1
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("having", total=self.group_by_count)

        for row in iterator:
            if task is not None:
                progress.update(task, total=self.group_by_count)

            include_row = True
            for having in self.definition["having"]:
                if not row.evaluate_expression(
                    having, self.definition.get("group_by"), self.functions,
                ):
                    include_row = False
                    break

            if include_row:
                self._having_count += 1
                yield row

            if task is not None:
                progress.update(task, advance=1)

    @property
    def having_count(self):
        return self._having_count

    def _process_sort_by(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        self._sort_by_count = 0
        if not self.definition.get("sort_by", []):
            for row in iterator:
                self._sort_by_count = self.having_count
                yield row
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task(
                "sort_by", total=len(self.definition["sort_by"]) * self.having_count
            )

        # First, materialize our list
        rows = list(iterator)
        if task is not None:
            progress.update(task, total=len(rows))
        self._sort_by_count = len(rows)

        # Now, sort by each of the ordering expressions in reverse order
        for sort_by in reversed(self.definition["sort_by"]):
            sort_expression, reverse = parse_sort_by_definition(sort_by)

            def sort_key(row):
                result = row.evaluate_expression(
                    sort_expression, self.definition.get("group_by"), self.functions
                )
                if task is not None:
                    progress.update(task, advance=1)

                return NullAcceptableSort(result)

            rows = sorted(rows, key=sort_key, reverse=reverse)

        yield from rows

    @property
    def sort_by_count(self):
        return self._sort_by_count

    def _generate_row_dict(self, row: Result) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.get_fields():
            result[field_defn["column"]] = row.evaluate_expression(
                field_defn["expression"],
                self.definition.get("group_by"),
                self.functions,
            )

        return result

    def _get_iterator(self, progress: Progress) -> Generator[Result, None, None]:
        source = self.definition["from"]

        if source == "issues":
            iterator = self._get_issues
        else:
            raise NotImplementedError(f"No search for source {source} implemented.")

        yield from self._process_sort_by(
            self._process_having(
                self._process_group_by(iterator(progress), progress), progress
            ),
            progress,
        )

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        with Progress(auto_refresh=self.progress_bar_enabled) as progress:
            task: Optional[TaskID] = None
            if self.progress_bar_enabled:
                task = progress.add_task("select", total=self.sort_by_count)
            for row in self._get_iterator(progress):
                if task is not None:
                    progress.update(task, total=self.sort_by_count)
                yield self._generate_row_dict(row)
                if task is not None:
                    progress.update(task, advance=1)
