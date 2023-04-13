from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from functools import total_ordering
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union
from typing import cast

from dotmap import DotMap
from jira import JIRA
from pydantic import BaseModel
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import TaskID
from rich.progress import TimeRemainingColumn

from . import __version__
from .cache import MinimumRecencyCache
from .exceptions import ExpressionParameterMissing
from .plugin import BaseSource
from .plugin import get_installed_functions
from .plugin import get_installed_sources
from .types import Expression
from .types import ExpressionList
from .types import Field
from .types import JqlList
from .types import QueryDefinition
from .types import SchemaRow
from .types import SelectFieldDefinition
from .types import WhereParamDict
from .utils import calculate_result_hash
from .utils import evaluate_expression
from .utils import expression_includes_group_by
from .utils import find_missing_parameters
from .utils import find_used_parameters
from .utils import get_cache_path
from .utils import get_field_data
from .utils import get_row_dict
from .utils import normalize_value
from .utils import parse_select_definition
from .utils import parse_sort_by_definition


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
    def __init__(self):
        self._overlay: dict[str, Any] = {}

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
        field_name_map: Optional[Dict[str, Any]] = None,
        functions: Optional[Dict[str, Callable]] = None,
    ):
        params: Dict[str, str] = cast(
            Dict[str, str],
            field_name_map.get("params", {}) if field_name_map is not None else {},
        )
        if missing := find_missing_parameters(
            expression,
            list(params.keys()),
        ):
            raise ExpressionParameterMissing(
                "Parameter {params.%s} found in expression, but no parameter was specified!"
                % missing[0]
            )

        if group_by is None:
            group_by = []

        row_source = self

        # Force returning a single value if the expression under
        # evaluation is one we're grouping on
        if expression_includes_group_by(expression, group_by):
            row_source = self.single()

        return get_field_data(
            row_source,
            expression,
            functions=functions,
            interpolations=field_name_map,
        )

    def __setitem__(self, name, value):
        self._overlay[name] = value


class SingleResult(Result):
    def __init__(self, row: Any):
        self._row = row
        super().__init__()

    def as_dict(self) -> Dict[str, Any]:
        return get_row_dict(self._row, self._overlay)

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
        self,
        rows: List[SingleResult] = None,
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
        result.update(self._overlay)

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


class CachedResults(BaseModel):
    source_schema: List[SchemaRow]
    rows: List[Dict]


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

    def _get_select_calculate_fields(
        self, field_data: List[Field] | Mapping[str, str | None]
    ) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        if isinstance(field_data, str):
            field = field_data
            if field == "*":
                fields.extend(self._get_all_fields())
            else:
                fields.append(parse_select_definition(field))
        if isinstance(field_data, dict):
            for column, expression in field_data.items():
                fields.append(
                    SelectFieldDefinition(
                        expression=expression if expression else column, column=column
                    )
                )
        elif isinstance(field_data, list):
            for field in field_data:
                if field == "*":
                    fields.extend(self._get_all_fields())
                else:
                    fields.append(parse_select_definition(field))

        return fields

    @property
    def select(self) -> List[SelectFieldDefinition]:
        return self._get_select_calculate_fields(self._definition.select)

    @property
    def static(self) -> List[SelectFieldDefinition]:
        return self._get_select_calculate_fields(self._definition.static)

    @property
    def calculate(self) -> List[SelectFieldDefinition]:
        return self._get_select_calculate_fields(self._definition.calculate)

    @property
    def from_(self) -> str:
        return self._definition.from_

    @property
    def subqueries(self) -> dict[str, "QueryDefinition"]:
        return {
            subquery_name: QueryDefinition.parse_obj(subquery_value)
            for subquery_name, subquery_value in self._definition.subqueries.items()
        }

    @property
    def where(self) -> Union[JqlList, WhereParamDict]:
        where = self._definition.where
        if isinstance(where, list):
            return self._ensure_str(where)
        return where

    @property
    def order_by(self) -> JqlList:
        return self._ensure_str(self._definition.order_by)

    @property
    def filter(self) -> ExpressionList:
        return self._ensure_str(self._definition.filter_)

    @property
    def having(self) -> ExpressionList:
        return self._ensure_str(self._definition.having)

    @property
    def group_by(self) -> ExpressionList:
        return self._ensure_str(self._definition.group_by)

    @property
    def sort_by(self) -> List[Tuple[Expression, bool]]:
        return [
            parse_sort_by_definition(definition)
            for definition in self._ensure_str(self._definition.sort_by)
        ]

    @property
    def expand(self) -> List[str]:
        return self._ensure_str(self._definition.expand)

    @property
    def limit(self) -> Optional[int]:
        return self._definition.limit

    @property
    def cap(self) -> Optional[int]:
        return self._definition.cap

    @property
    def cache(self) -> Optional[Tuple[Optional[int], Optional[int]]]:
        value = self._definition.cache
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


class CounterChannel:
    def __init__(self):
        self._counter: int = 2**32

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
        parameters: Optional[Dict[str, Any]] = None,
        schema: Optional[List[SchemaRow]] = None,
    ):
        self._query: Query = Query(jira, definition)
        self._jira: JIRA = jira
        self._functions: Dict[str, Callable] = get_installed_functions(jira, self)
        self._progress_bar_enabled = progress_bar

        self._enable_cache = enable_cache
        self._cache = MinimumRecencyCache(get_cache_path())
        self._source_schema: List[SchemaRow] = schema if schema is not None else []
        self._field_name_map: Dict[str, str] = FieldNameMap()

        self._parameters: Dict[str, Any] = parameters or {}

    @property
    def jira(self) -> JIRA:
        return self._jira

    @property
    def schema(self) -> List[SchemaRow]:
        return self._source_schema

    @property
    def cache(self) -> MinimumRecencyCache:
        return self._cache

    @property
    def query(self) -> Query:
        return self._query

    @property
    def functions(self) -> Dict[str, Callable]:
        return self._functions

    @property
    def parameters(self) -> Dict[str, Any]:
        return self._parameters

    def get_source_schema(self) -> List[SchemaRow]:
        if not self._source_schema:
            sources = get_installed_sources()
            source = sources[self.query.from_]

            self._source_schema = source.get_schema(self.jira)

        return self._source_schema

    @property
    def field_name_map(self) -> Dict[str, Any]:
        if not self._field_name_map:
            for schema_row in self.get_source_schema():
                if not schema_row.description:
                    continue

                self._field_name_map[schema_row.description] = schema_row.id

            self._field_name_map["params"] = DotMap(self._parameters)

        return self._field_name_map

    def _get_cached(self, source: BaseSource) -> Iterator[Result]:
        cache_key = ":".join(
            [
                __version__,
                str(self.jira.client_info()),
                str(self.query.from_),
                str(self.query.where),
                str(self.query.order_by),
                str(self.query.limit),
                str(self.query.expand),
                str(
                    {
                        key: value
                        for key, value in self.parameters.items()
                        if key in find_used_parameters("".join(self.query.where))
                    }
                ),
            ]
        )

        if self.query.cache and self._enable_cache:
            try:
                min_recency, _ = self.query.cache
                if min_recency is None:
                    raise KeyError(cache_key)
                cached_results_raw = self.cache.get(cache_key, min_recency=min_recency)
                if not cached_results_raw:
                    raise KeyError(cache_key)

                cached_results = CachedResults.parse_obj(cached_results_raw)

                self._source_schema = cached_results.source_schema

                source.update_count(len(cached_results.rows))
                source.remove_progress()
                for result in cached_results.rows:
                    yield SingleResult(source.rehydrate(result))
                return
            except KeyError:
                pass

        cached_rows = []
        cached_schema = self.get_source_schema()

        for result in source:
            cached_rows.append(result)
            yield SingleResult(source.rehydrate(result))

        if self.query.cache:
            _, max_store = self.query.cache
            if max_store is not None:
                self.cache.set(
                    cache_key,
                    CachedResults(source_schema=cached_schema, rows=cached_rows).dict(),
                    expire=max_store,
                )

    def _get_static_results(
        self,
    ) -> Dict[str, Any]:
        shared: Dict[str, Any] = {}

        for definition in self.query.static:
            if missing := find_missing_parameters(
                definition.expression, list(self.parameters.keys())
            ):
                raise ExpressionParameterMissing(
                    "Parameter {params.%s} found in expression, but no parameter was specified!"
                    % missing[0]
                )

            shared[definition.column] = normalize_value(
                evaluate_expression(
                    definition.expression,
                    names={},
                    functions=self.functions,
                    interpolations={"params": DotMap(self.parameters)},
                )
            )

        return shared

    def _process_calculate(
        self,
        iterator: Iterator[Result],
        task: TaskID,
        input_channel: CounterChannel,
        output_channel: CounterChannel,
    ) -> Iterator[Result]:
        for row in iterator:
            output_channel.set(input_channel.get())
            self.progress.update(task, total=input_channel.get(), visible=True)

            for definition in self.query.calculate:
                row[definition.column] = self.evaluate_expression(
                    row, definition.expression
                )

            yield row

            self.progress.update(task, advance=1)

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

            row_hash = calculate_result_hash(
                row,
                self.query.group_by,
                self.functions,
            )
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
            result[field_defn.column] = self.evaluate_expression(
                row,
                field_defn.expression,
            )

        return result

    def _get_iterator(self) -> Generator[Dict[str, Any], None, None]:
        sources = get_installed_sources()

        static_results = self._get_static_results()

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
                    [
                        Iterator[Result],
                        TaskID,
                        CounterChannel,
                        CounterChannel,
                    ],
                    Iterator[Result],
                ],
                TaskID,
            ]
        ] = []
        if self.query.calculate:
            calculate_task = self.progress.add_task("calculate", total=0, visible=False)
            phases.append((self._process_calculate, calculate_task))
        if self.query.filter:
            filter_task = self.progress.add_task("filter", total=0, visible=False)
            phases.append(
                (
                    self._process_filter,
                    filter_task,
                ),
            )
        if self.query.group_by:
            group_by_task = self.progress.add_task("group_by", total=0, visible=False)
            phases.append(
                (
                    self._process_group_by,
                    group_by_task,
                ),
            )
        if self.query.having:
            having_task = self.progress.add_task("having", total=0, visible=False)
            phases.append(
                (
                    self._process_having,
                    having_task,
                ),
            )
        if self.query.sort_by:
            sort_by_task = self.progress.add_task("sort_by", total=0, visible=False)
            phases.append(
                (
                    self._process_sort_by,
                    sort_by_task,
                ),
            )
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

            for shared_result_name, shared_result_value in static_results.items():
                row[shared_result_name] = shared_result_value

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
