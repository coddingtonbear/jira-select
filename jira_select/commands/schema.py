import argparse
import json
from typing import Any
from typing import Callable
from typing import Dict

from rich.table import Table

from ..exceptions import JiraSelectError
from ..plugin import BaseCommand
from ..plugin import get_installed_functions
from ..plugin import get_installed_sources
from ..utils import JiraSelectJsonEncoder
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
            "source",
            choices=list(sources.keys()),
        )
        parser.add_argument(
            "search_terms",
            nargs="*",
            type=str,
            help="Case-insensitive search term for limiting displayed results.",
        )
        parser.add_argument(
            "--json",
            "-j",
            default=False,
            action="store_true",
            help="Export schema as JSON format instead of printing a table.",
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

        if self.options.json:
            fields = []
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
                    if not self.evaluate_expression(row, self.options.having):
                        continue

                fields.append(
                    {
                        "id": row.id,
                        "type": row.type,
                        "description": row.description,
                    }
                )
            self.console.print(
                json.dumps(fields, cls=JiraSelectJsonEncoder, sort_keys=True, indent=4)
            )
        else:
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
                    if not self.evaluate_expression(row, self.options.having):
                        continue

                table.add_row(row.id, row.type, row.description)

            self.console.print(table)
