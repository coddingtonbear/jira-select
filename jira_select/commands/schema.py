import argparse
from typing import Any, Callable, Dict, Iterable

from dotmap import DotMap
from rich.table import Table
from simpleeval import NameNotDefined

from ..exceptions import JiraSelectError
from ..plugin import BaseCommand, get_installed_functions
from ..types import SchemaRow
from ..utils import get_field_data


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.functions: Dict[str, Callable] = get_installed_functions(self.jira)

    @classmethod
    def get_help(cls) -> str:
        return "Searches Jira for fields matching your search query."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "source", choices=["issues"],
        )
        parser.add_argument(
            "--having",
            help=(
                "A 'having' expression to use for limiting the displayed results. "
                "Searchable fields are 'key', 'type', and 'description'. "
                "E.g.--having=\"'estimate' in description.lower()\". "
            ),
        )

    def evaluate_expression(self, row: Any, expression: str) -> Any:
        return get_field_data(row, expression, functions=self.functions)

    def get_field_data(self, row: Any, expression: str) -> str:
        result = self.evaluate_expression(row, expression)
        if isinstance(result, str):
            return result
        return ""

    def get_issue_data(self) -> Iterable[SchemaRow]:
        for column in sorted(self.jira.fields(), key=lambda field: field["name"]):
            try:
                type = str(self.get_field_data(DotMap(column), "schema.type"))
            except NameNotDefined:
                type = ""
            data: SchemaRow = {
                "key": str(self.get_field_data(DotMap(column), "key")),
                "type": type,
                "description": str(self.get_field_data(DotMap(column), "name")),
            }
            yield data

    def handle(self) -> None:
        source_data_fns: Dict[str, Callable[[], Iterable[SchemaRow]]] = {
            "issues": self.get_issue_data
        }

        try:
            data_fn = source_data_fns[self.options.source]
        except KeyError:
            raise JiraSelectError(
                f"No source data function defined for {self.options.source}"
            )

        table = Table(title=self.options.source)
        table.add_column(header="key", style="green")
        table.add_column(header="type", style="cyan")
        table.add_column(header="description", style="bright_cyan")

        for row in data_fn():
            if self.options.having:
                do_show = self.evaluate_expression(DotMap(row), self.options.having)
                if not do_show:
                    continue

            table.add_row(
                row["key"], row["type"], row["description"],
            )

        self.console.print(table)
