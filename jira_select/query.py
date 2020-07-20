from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import total_ordering
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    cast,
    Iterable,
    Tuple,
    Type,
    Union,
)

from jira import JIRA, Issue
from rich.progress import Progress, TaskID

from .plugin import get_installed_functions
from .types import (
    ExpressionList,
    JqlList,
    QueryDefinition,
    SelectFieldDefinition,
    Expression,
)
from .utils import (
    calculate_result_hash,
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

        try:
            return self._value == other._value
        except Exception:
            return False

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
    def __init__(self, jira: JIRA, definition: QueryDefinition):
        self._jira = jira
        self._definition = definition

    def _ensure_str(self, iterable=Iterable[Any]) -> List[str]:
        return [str(item) for item in iterable]

    def _get_all_fields(self):
        fields = [{"id": "key"}, {"id": "id"}] + self._jira.fields()
        for field in fields:
            definition: SelectFieldDefinition = {
                "expression": field["id"],
                "column": field["id"],
            }
            yield definition

    @property
    def select(self) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for field in self._definition["select"]:
            if field == "*":
                fields.extend(self._get_all_fields())
            else:
                fields.append(parse_select_definition(field))

        return fields

    @property
    def from_(self) -> str:
        return self._definition["from"]

    @property
    def where(self) -> JqlList:
        return self._ensure_str(self._definition.get("where", []))

    @property
    def order_by(self) -> JqlList:
        return self._ensure_str(self._definition.get("order_by", []))

    @property
    def having(self) -> ExpressionList:
        return self._ensure_str(self._definition.get("having", []))

    @property
    def group_by(self) -> ExpressionList:
        return self._ensure_str(self._definition.get("group_by", []))

    @property
    def sort_by(self) -> List[Tuple[Expression, bool]]:
        return [
            parse_sort_by_definition(definition)
            for definition in self._ensure_str(self._definition.get("sort_by", []))
        ]

    @property
    def expand(self) -> List[str]:
        return self._ensure_str(self._definition.get("expand", []))

    @property
    def limit(self) -> Optional[int]:
        return self._definition.get("limit")

    @property
    def cap(self) -> Optional[int]:
        return self._definition.get("cap")


class NullProgressbar:
    def update(self, *args, **kwargs):
        pass

    def add_task(self, *args, **kwargs) -> TaskID:
        return TaskID(0)

    def __enter__(self) -> NullProgressbar:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class Executor:
    def __init__(
        self, jira: JIRA, definition: QueryDefinition, progress_bar: bool = False
    ):
        self._query: Query = Query(jira, definition)
        # self._definition: QueryDefinition = clean_query_definition(definition)
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)
        self._progress_bar_enabled = progress_bar

        # Set a high ceiling at the start so the progressbar does not
        # start "full"
        self._jira_count = 2 ** 32
        self._group_by_count = 2 ** 32
        self._having_count = 2 ** 32
        self._sort_by_count = 2 ** 32

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def query(self) -> Query:
        return self._query

    @property
    def functions(self) -> Dict[str, Callable]:
        return self._functions

    def _get_jql(self) -> str:
        query = " AND ".join(self.query.where)
        order_by_fields = ", ".join(self.query.order_by)

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def _get_issues(self, task: TaskID) -> Generator[SingleResult, None, None]:
        jql = self._get_jql()

        start_at = 0
        max_results = 2 ** 32
        result_limit = self.query.limit or 2 ** 32

        while start_at < max_results:
            results = self.jira.search_issues(
                jql,
                startAt=start_at,
                expand=",".join(self.query.expand),
                fields="*all",
                maxResults=min(result_limit, 100),
            )
            max_results = results.total
            self._jira_count = min(results.total, result_limit)
            for result in results:
                result = cast(Issue, result)
                self.progress.update(task, advance=1, total=self.jira_count)

                start_at += 1
                yield SingleResult(result)

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    return

    @property
    def jira_count(self):
        return self._jira_count

    def _process_group_by(
        self, iterator: Generator[SingleResult, None, None], task: Optional[TaskID]
    ) -> Generator[Result, None, None]:
        groups: Dict[int, GroupedResult] = {}
        self._group_by_count = 0

        if not self.query.group_by:
            for row in iterator:
                self._group_by_count = self.jira_count
                yield row
            return

        assert task is not None

        for row in iterator:
            self.progress.update(task, total=self.jira_count)

            row_hash = calculate_result_hash(row, self.query.group_by, self.functions,)
            if row_hash not in groups:
                self._group_by_count += 1
                groups[row_hash] = GroupedResult()

            groups[row_hash].add(row)

            self.progress.update(task, advance=1)

        for _, value in groups.items():
            yield value

    @property
    def group_by_count(self):
        return self._group_by_count

    def _process_having(
        self, iterator: Generator[Result, None, None], task: Optional[TaskID]
    ) -> Generator[Result, None, None]:
        self._having_count = 0
        if not self.query.having:
            for row in iterator:
                self._having_count = self.group_by_count
                yield row
            return

        assert task is not None

        for row in iterator:
            self.progress.update(task, total=self.group_by_count)

            include_row = True
            for having in self.query.having:
                if not row.evaluate_expression(
                    having, self.query.group_by, self.functions,
                ):
                    include_row = False
                    break

            if include_row:
                self._having_count += 1
                yield row

            self.progress.update(task, advance=1)

    @property
    def having_count(self):
        return self._having_count

    def _process_sort_by(
        self, iterator: Generator[Result, None, None], task: Optional[TaskID],
    ) -> Generator[Result, None, None]:
        self._sort_by_count = 0
        if not self.query.sort_by:
            for row in iterator:
                self._sort_by_count = self.having_count
                yield row
            return

        assert task is not None

        # First, materialize our list
        rows = list(iterator)
        self.progress.update(task, total=len(rows))
        self._sort_by_count = len(rows)

        # Now, sort by each of the ordering expressions in reverse order
        for sort_expression, reverse in reversed(self.query.sort_by):

            def sort_key(row):
                result = row.evaluate_expression(
                    sort_expression, self.query.group_by, self.functions
                )
                self.progress.update(task, advance=1)

                return NullAcceptableSort(result)

            rows = sorted(rows, key=sort_key, reverse=reverse)

        yield from rows

    @property
    def sort_by_count(self):
        return self._sort_by_count

    def _generate_row_dict(self, row: Result) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.query.select:
            result[field_defn["column"]] = row.evaluate_expression(
                field_defn["expression"], self.query.group_by, self.functions,
            )

        return result

    def _get_iterator(self) -> Generator[Dict[str, Any], None, None]:
        iterator_task = self.progress.add_task("jira", total=2 ** 32)
        group_by_task: Optional[TaskID] = None
        if self.query.group_by:
            group_by_task = self.progress.add_task("group_by", total=2 ** 32)
        having_task: Optional[TaskID] = None
        if self.query.having:
            having_task = self.progress.add_task("having", total=2 ** 32)
        sort_by_task: Optional[TaskID] = None
        if self.query.sort_by:
            sort_by_task = self.progress.add_task("sort_by", total=2 ** 32)
        select_task = self.progress.add_task("select", total=2 ** 32)

        if self.query.from_ == "issues":
            iterator = self._get_issues
        else:
            raise NotImplementedError(
                f"No search for source {self.query.from_} implemented."
            )

        for row in self._process_sort_by(
            self._process_having(
                self._process_group_by(iterator(iterator_task), group_by_task),
                having_task,
            ),
            sort_by_task,
        ):
            self.progress.update(select_task, total=self.sort_by_count)
            yield self._generate_row_dict(row)
            self.progress.update(select_task, advance=1)

    @property
    def progress(self) -> Union[Progress, NullProgressbar]:
        return self._progress_bar

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        progress_bar_cls: Union[Type[Progress], Type[NullProgressbar]] = NullProgressbar
        if self._progress_bar_enabled:
            progress_bar_cls = Progress

        with progress_bar_cls() as progress:
            self._progress_bar = progress

            row_count = 0
            for row in self._get_iterator():
                yield row

                row_count += 1
                if self.query.cap is not None and row_count >= self.query.cap:
                    break
