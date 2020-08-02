import argparse
from typing import Any, Callable, Dict

from dotmap import DotMap
from rich.table import Table

from ..exceptions import JiraSelectError
from ..plugin import BaseCommand, get_installed_functions, get_installed_sources
from ..utils import evaluate_expression


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.functions: Dict[str, Callable] = get_installed_functions(self.jira)

    @classmethod
    def get_help(cls) -> str:
        return (
            "Describes the fields available in data returned from "
            "a particular data source."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        sources = get_installed_sources()

        parser.add_argument(
            "source", choices=list(sources.keys()),
        )
        parser.add_argument(
            "search_terms",
            nargs="*",
            type=str,
            help="Case-insensitive search term for limiting displayed results.",
        )
        parser.add_argument(
            "--having",
            help=(
                "A 'having' expression to use for limiting the displayed results. "
                "Searchable fields are 'key', 'type', and 'description' and 'raw'. "
                "E.g.--having=\"'estimate' in description.lower()\". "
            ),
        )

    def evaluate_expression(self, row: Any, expression: str) -> Any:
        return evaluate_expression(expression, row, functions=self.functions)

    def handle(self) -> None:
        sources = get_installed_sources()

        try:
            source = sources[self.options.source]
        except KeyError:
            raise JiraSelectError(f"No source named '{self.options.source}' found.")

        table = Table(title=self.options.source)
        table.add_column(header="id", style="green")
        table.add_column(header="type", style="cyan")
        table.add_column(header="description", style="bright_cyan")

        for row in source.get_schema(self.jira):
            if self.options.search_terms:
                matches = True
                for option in self.options.search_terms:
                    if option.lower() not in str(row).lower():
                        matches = False
                        break
                if not matches:
                    continue
            if self.options.having:
                if not self.evaluate_expression(DotMap(row), self.options.having):
                    continue

            table.add_row(
                row.get("id", "Unknown"),
                row.get("type", "Unknown"),
                row.get("description", ""),
            )

        self.console.print(table)
