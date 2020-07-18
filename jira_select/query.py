from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Dict, Generator, List, Optional, cast

from jira import JIRA, Issue
from rich.progress import Progress, TaskID

from .plugin import get_installed_functions
from .types import QueryDefinition, SelectFieldDefinition
from .utils import (
    calculate_result_hash,
    clean_query_definition,
    expressions_match,
    get_field_data,
    get_row_dict,
    parse_sort_by_definition,
    parse_select_definition,
)


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
        self._select_count = 2 ** 32
        self._group_by_count = 2 ** 32
        self._having_count = 2 ** 32

    @property
    def progress_bar_enabled(self):
        return self._progress_bar

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def definition(self) -> QueryDefinition:
        return self._definition

    def get_functions(self) -> Dict[str, Callable]:
        return self._functions

    def get_fields(self) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for field in self.definition["select"]:
            fields.append(parse_select_definition(field))

        return fields

    def _generate_row_dict(self, row: Result) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.get_fields():
            return_singular = False
            for expression in self.definition.get("group_by", []):
                if expressions_match(field_defn["expression"], expression):
                    return_singular = True
                    break

            record = row
            if return_singular:
                record = row.single()

            result[field_defn["column"]] = get_field_data(
                record, field_defn["expression"], functions=self._functions
            )

        return result

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
            task = progress.add_task("select/where", total=self.select_count)

        while start_at < max_results:
            results = self.jira.search_issues(
                jql, startAt=start_at, expand=",".join(expand), fields="*all",
            )
            max_results = results.total
            self._select_count = min(results.total, result_limit)
            for result in results:
                result = cast(Issue, result)
                if task is not None:
                    progress.update(task, advance=1, total=self.select_count)

                yield SingleResult(result)
                start_at += 1

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    return

    @property
    def select_count(self):
        return self._select_count

    def _process_group_by(
        self, iterator: Generator[SingleResult, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        group_fields = self.definition.get("group_by", [])
        groups: Dict[int, GroupedResult] = {}
        self._group_by_count = 0

        if not group_fields:
            for row in iterator:
                yield row
                self._group_by_count += 1
            return

        task: Optional[TaskID] = None
        if self.progress_bar_enabled:
            task = progress.add_task("group_by", total=self.select_count)

        for row in iterator:
            row_hash = calculate_result_hash(row, group_fields, self._functions,)
            if row_hash not in groups:
                groups[row_hash] = GroupedResult()
                self._group_by_count += 1

            groups[row_hash].add(row)

            if task is not None:
                progress.update(task, advance=1, total=self.select_count)

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
            include_row = True
            for having in self.definition["having"]:
                if not get_field_data(row, having, self._functions):
                    include_row = False
                    break

            if include_row:
                yield row
                self._having_count += 1

            if task is not None:
                progress.update(task, advance=1, total=self.group_by_count)

    @property
    def having_count(self):
        return self._having_count

    def _process_sort_by(
        self, iterator: Generator[Result, None, None], progress: Progress
    ) -> Generator[Result, None, None]:
        if not self.definition.get("sort_by", []):
            yield from iterator
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

        # Now, sort by each of the ordering expressions in reverse order
        for sort_by in reversed(self.definition["sort_by"]):

            def sort_key(row):
                result = get_field_data(
                    row, parse_sort_by_definition(sort_by), self._functions
                )
                if task is not None:
                    progress.update(task, advance=1)

                return result

            rows = sorted(rows, key=sort_key)

        yield from rows

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
            for row in self._get_iterator(progress):
                yield self._generate_row_dict(row)
