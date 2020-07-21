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
from rich.progress import Progress, TaskID, BarColumn, TimeRemainingColumn
from diskcache import Cache

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
    get_cache_path,
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

    @property
    def cache(self) -> Optional[int]:
        return self._definition.get("cache")


class NullProgressbar:
    def __init__(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def add_task(self, *args, **kwargs) -> TaskID:
        return TaskID(0)

    def remove_task(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs) -> NullProgressbar:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class NullCache:
    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, key):
        raise KeyError(key)

    def get(self, key, default=None, **kwargs):
        return default

    def touch(self, key, **kwargs):
        return

    def set(self, key, value, **kwargs):
        return

    def add(self, key, value, **kwargs):
        return


class CounterChannel:
    def __init__(self):
        self._counter: int = 2 ** 32

    def zero(self):
        self._counter = 0

    def increment(self):
        self._counter += 1

    def set(self, value: int):
        self._counter = value

    def get(self) -> int:
        return self._counter


class Executor:
    def __init__(
        self,
        jira: JIRA,
        definition: QueryDefinition,
        enable_cache: bool = True,
        progress_bar: bool = False,
    ):
        self._query: Query = Query(jira, definition)
        # self._definition: QueryDefinition = clean_query_definition(definition)
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira)
        self._progress_bar_enabled = progress_bar

        self._cache: Union[Cache, NullCache] = NullCache()
        if enable_cache:
            self._cache = Cache(get_cache_path())

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def cache(self) -> Union[Cache, NullCache]:
        return self._cache

    @property
    def query(self) -> Query:
        return self._query

    @property
    def functions(self) -> Dict[str, Callable]:
        return self._functions

    def _get_jql(self) -> str:
        query = " AND ".join(f"({q})" for q in self.query.where)
        order_by_fields = ", ".join(self.query.order_by)

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def _get_issues(
        self, task: TaskID, out_channel: CounterChannel
    ) -> Generator[SingleResult, None, None]:
        jql = self._get_jql()
        cache_key = f"{jql}:{','.join(self.query.order_by)}:{self.query.limit}"

        start_at = 0
        max_results = 2 ** 32
        result_limit = self.query.limit or 2 ** 32

        if self.query.cache:
            try:
                cached_results = self.cache[cache_key]
                out_channel.set(len(cached_results))
                self.progress.remove_task(task)
                for result in cached_results:
                    yield SingleResult(Issue({}, None, result))
                return
            except KeyError:
                pass

        cache = []

        self.progress.update(task, completed=0, total=1, visible=True)
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
            out_channel.set(count)

            for result in results:
                result = cast(Issue, result)
                self.progress.update(task, advance=1, total=count, visible=True)

                if self.query.cache:
                    cache.append(result.raw)

                start_at += 1
                yield SingleResult(result)

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    break

        if self.query.cache:
            self.cache.set(cache_key, cache, expire=self.query.cache)

    def _process_group_by(
        self,
        iterator: Generator[SingleResult, None, None],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Generator[Result, None, None]:
        groups: Dict[int, GroupedResult] = {}

        output_channel.zero()

        for row in iterator:
            self.progress.update(task, total=input_channel.get(), visible=True)

            row_hash = calculate_result_hash(row, self.query.group_by, self.functions,)
            if row_hash not in groups:
                output_channel.increment()
                groups[row_hash] = GroupedResult()

            groups[row_hash].add(row)

            self.progress.update(task, advance=1)

        for _, value in groups.items():
            yield value

    def _process_having(
        self,
        iterator: Generator[Result, None, None],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Generator[Result, None, None]:
        output_channel.zero()

        for row in iterator:
            self.progress.update(task, total=input_channel.get(), visible=True)

            include_row = True
            for having in self.query.having:
                if not row.evaluate_expression(
                    having, self.query.group_by, self.functions,
                ):
                    include_row = False
                    break

            if include_row:
                output_channel.increment()
                yield row

            self.progress.update(task, advance=1)

    def _process_sort_by(
        self,
        iterator: Generator[Result, None, None],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Generator[Result, None, None]:
        # First, materialize our list
        rows = list(iterator)
        output_channel.set(len(rows))
        self.progress.update(task, total=len(rows), visible=True)

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

    def _generate_row_dict(self, row: Result) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.query.select:
            result[field_defn["column"]] = row.evaluate_expression(
                field_defn["expression"], self.query.group_by, self.functions,
            )

        return result

    def _get_iterator(self) -> Generator[Dict[str, Any], None, None]:
        if self.query.from_ == "issues":
            iterator = self._get_issues
        else:
            raise NotImplementedError(
                f"No search for source {self.query.from_} implemented."
            )

        # Do not show the counters until we know how many rows they have waiting
        iterator_task = self.progress.add_task("jira", total=0, visible=False)
        phases = []
        if self.query.group_by:
            group_by_task = self.progress.add_task("group_by", total=0, visible=False)
            phases.append((self._process_group_by, group_by_task,),)
        if self.query.having:
            having_task = self.progress.add_task("having", total=0, visible=False)
            phases.append((self._process_having, having_task,),)
        if self.query.sort_by:
            sort_by_task = self.progress.add_task("sort_by", total=0, visible=False)
            phases.append((self._process_sort_by, sort_by_task,),)
        select_task = self.progress.add_task("select", total=0, visible=False)

        # Link up each generator with its source; these will vary
        # depending on what query feature are in use
        channel = CounterChannel()
        cursor: Generator = iterator(iterator_task, channel)
        for phase, task_id in phases:
            output_channel = CounterChannel()
            cursor = phase(cursor, task_id, channel, output_channel)
            channel = output_channel

        for row in cursor:
            self.progress.update(select_task, total=channel.get(), visible=True)
            yield self._generate_row_dict(row)
            self.progress.update(select_task, advance=1)

    @property
    def progress(self) -> Union[Progress, NullProgressbar]:
        return self._progress_bar

    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        progress_bar_cls: Union[Type[Progress], Type[NullProgressbar]] = NullProgressbar
        if self._progress_bar_enabled:
            progress_bar_cls = Progress

        with progress_bar_cls(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[medium_purple4]{task.completed}/{task.total}[/medium_purple4]",
            TimeRemainingColumn(),
        ) as progress:
            self._progress_bar = progress

            row_count = 0
            for row in self._get_iterator():
                yield row

                row_count += 1
                if self.query.cap is not None and row_count >= self.query.cap:
                    break
