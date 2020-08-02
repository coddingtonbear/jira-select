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
    Iterable,
    Iterator,
    Tuple,
    Type,
    Union,
)

from jira import JIRA, Issue
from rich.progress import Progress, TaskID, BarColumn, TimeRemainingColumn

from .cache import MinimumRecencyCache
from .plugin import BaseSource, get_installed_functions, get_installed_sources
from .types import (
    ExpressionList,
    JqlList,
    QueryDefinition,
    SelectFieldDefinition,
    Expression,
    WhereParamDict,
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
        group_by: Optional[ExpressionList] = None,
        field_name_map: Optional[Dict[str, str]] = None,
        functions: Optional[Dict[str, Callable]] = None,
    ):
        if group_by is None:
            group_by = []

        row_source = self

        # Force returning a single value if the expression under
        # evaluation is one we're grouping on
        if expression_includes_group_by(expression, group_by):
            row_source = self.single()

        return get_field_data(
            row_source, expression, functions=functions, interpolations=field_name_map,
        )


class SingleResult(Result):
    def __init__(self, row: Any):
        self._row = row

    def as_dict(self) -> Dict[str, Any]:
        return get_row_dict(self._row)

    def single(self) -> SingleResult:
        return self


class GroupedFieldContainer(list):
    def __getattr__(self, name):
        results = GroupedFieldContainer()

        for row in self:
            value = getattr(row, name, None)
            if value is not None:
                results.append(value)

        return results


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
            result[field] = GroupedFieldContainer(
                [
                    row.as_dict()[field]
                    for row in self._rows
                    if row.as_dict().get(field) is not None
                ]
            )

        return result


class Query:
    def __init__(self, jira: JIRA, definition: QueryDefinition):
        self._jira = jira
        self._definition = definition

    def _ensure_str(self, iterable=Iterable[Any]) -> List[str]:
        return [str(item) for item in iterable]

    def _get_all_fields(self) -> List[SelectFieldDefinition]:
        sources = get_installed_sources()

        try:
            source = sources[self.from_]
        except KeyError:
            return []

        return source.get_all_fields(self._jira)

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
    def where(self) -> Union[JqlList, WhereParamDict]:
        where = self._definition.get("where", [])
        if isinstance(where, list):
            return self._ensure_str(where)
        return where

    @property
    def order_by(self) -> JqlList:
        return self._ensure_str(self._definition.get("order_by", []))

    @property
    def filter(self) -> ExpressionList:
        return self._ensure_str(self._definition.get("filter", []))

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
    def cache(self) -> Optional[Tuple[Optional[int], Optional[int]]]:
        value = self._definition.get("cache")
        if isinstance(value, int):
            return (
                value,
                value,
            )
        return value


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

    def get(self, key, default=None, **kwargs) -> Optional[Any]:
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


class FieldNameMap(dict):
    def __missing__(self, key):
        return key


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

        self._cache: Union[MinimumRecencyCache, NullCache] = NullCache()
        if enable_cache:
            self._cache = MinimumRecencyCache(get_cache_path())

        self._field_name_map: Dict[str, str] = FieldNameMap()

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def cache(self) -> Union[MinimumRecencyCache, NullCache]:
        return self._cache

    @property
    def query(self) -> Query:
        return self._query

    @property
    def functions(self) -> Dict[str, Callable]:
        return self._functions

    @property
    def field_name_map(self) -> Dict[str, str]:
        if not self._field_name_map:
            for jira_field in self.jira.fields():
                self._field_name_map[jira_field["name"]] = jira_field["id"]

        return self._field_name_map

    def _get_jql(self) -> str:
        query = " AND ".join(f"({q})" for q in self.query.where)
        order_by_fields = ", ".join(self.query.order_by)

        if order_by_fields:
            query = f"{query} ORDER BY {order_by_fields}"

        return query

    def _get_cached(self, source: BaseSource) -> Iterator[Result]:
        cache_key = ":".join(
            [
                str(self.jira.client_info()),
                str(self.query.from_),
                str(self.query.where),
                str(self.query.order_by),
                str(self.query.limit),
                str(self.query.expand),
            ]
        )

        if self.query.cache:
            try:
                min_recency, _ = self.query.cache
                if min_recency is None:
                    raise KeyError(cache_key)
                cached_results = self.cache.get(cache_key, min_recency=min_recency)
                if not cached_results:
                    raise KeyError(cache_key)

                source.update_count(len(cached_results))
                source.remove_progress()
                for result in cached_results:
                    yield SingleResult(Issue({}, None, result))
                return
            except KeyError:
                pass

        cache = []

        for result in source:
            cache.append(result)
            yield SingleResult(source.rehydrate(result))

        if self.query.cache:
            _, max_store = self.query.cache
            if max_store is not None:
                self.cache.set(cache_key, cache, expire=max_store)

    def _process_filter(
        self,
        iterator: Iterator[Result],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Iterator[Result]:
        output_channel.zero()

        for row in iterator:
            self.progress.update(task, total=input_channel.get(), visible=True)

            include_row = True
            for filter_expression in self.query.filter:
                if not self.evaluate_expression(row, filter_expression):
                    include_row = False
                    break

            if include_row:
                output_channel.increment()
                yield row

            self.progress.update(task, advance=1)

    def _process_group_by(
        self,
        iterator: Iterator[Result],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Iterator[Result]:
        groups: Dict[int, Result] = {}

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
        iterator: Iterator[Result],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Iterator[Result]:
        output_channel.zero()

        for row in iterator:
            self.progress.update(task, total=input_channel.get(), visible=True)

            include_row = True
            for having in self.query.having:
                if not self.evaluate_expression(row, having):
                    include_row = False
                    break

            if include_row:
                output_channel.increment()
                yield row

            self.progress.update(task, advance=1)

    def _process_sort_by(
        self,
        iterator: Iterator[Result],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Iterator[Result]:
        # First, materialize our list
        rows = list(iterator)
        output_channel.set(len(rows))
        self.progress.update(task, total=len(rows), visible=True)

        # Now, sort by each of the ordering expressions in reverse order
        for sort_expression, reverse in reversed(self.query.sort_by):

            def sort_key(row):
                result = self.evaluate_expression(row, sort_expression)
                self.progress.update(task, advance=1)

                return NullAcceptableSort(result)

            rows = sorted(rows, key=sort_key, reverse=reverse)

        yield from rows

    def _generate_row_dict(self, row: Result) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field_defn in self.query.select:
            result[field_defn["column"]] = self.evaluate_expression(
                row, field_defn["expression"],
            )

        return result

    def _get_iterator(self) -> Generator[Dict[str, Any], None, None]:
        sources = get_installed_sources()

        try:
            iterator = sources[self.query.from_]
        except KeyError:
            raise NotImplementedError(
                f"No search for source {self.query.from_} implemented."
            )

        # Do not show the counters until we know how many rows they have waiting
        iterator_task = self.progress.add_task("jira", total=0, visible=False)
        phases: List[
            Tuple[
                Callable[
                    [Iterator[Result], TaskID, CounterChannel, CounterChannel,],
                    Iterator[Result],
                ],
                TaskID,
            ]
        ] = []
        if self.query.filter:
            filter_task = self.progress.add_task("filter", total=0, visible=False)
            phases.append((self._process_filter, filter_task,),)
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
        cursor: Iterator = self._get_cached(iterator(self, iterator_task, channel))
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

    def evaluate_expression(self, row: Result, expression: Expression) -> Any:
        return row.evaluate_expression(
            expression,
            self.query.group_by,
            functions=self.functions,
            field_name_map=self.field_name_map,
        )

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
