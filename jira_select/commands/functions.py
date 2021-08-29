import argparse
import inspect
import json

from rich.table import Table

from ..plugin import BaseCommand
from ..plugin import get_installed_functions
from ..utils import evaluate_expression


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Lists all available functions, their signatures, and description."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
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
            help="Export functions in JSON format instead of printing a table.",
        )
        parser.add_argument(
            "--having",
            help=(
                "A 'having' expression to use for limiting the displayed results. "
                "Searchable fields are 'name' and 'description'. "
                "E.g.--having=\"'average' in description.lower()\". "
            ),
        )

    def handle(self):
        functions = get_installed_functions(self.jira)

        if self.options.json:
            function_data = []
            for name, fn in functions.items():
                docstring = fn.__doc__ or ""

                row = {
                    "name": name,
                    "description": docstring,
                }
                try:
                    row["signature"] = str(inspect.signature(fn))
                except Exception:
                    pass

                if self.options.search_terms:
                    matches = True
                    for option in self.options.search_terms:
                        if option.lower() not in str(row).lower():
                            matches = False
                            break
                    if not matches:
                        continue
                if self.options.having:
                    if not evaluate_expression(self.options.having, row, functions):
                        continue

                function_data.append(row)
            self.console.print(json.dumps(function_data, sort_keys=True, indent=4))
        else:
            table = Table(title="functions")
            table.add_column(header="name", style="green")
            table.add_column(header="description", style="white")

            for name, fn in functions.items():
                docstring = fn.__doc__ or ""

                try:
                    signature = (
                        f"[bright_cyan]{name}{inspect.signature(fn)}[/bright_cyan]\n\n"
                    )
                except Exception:
                    signature = ""

                description = signature + docstring.strip() + "\n\n"

                row = {
                    "name": name,
                    "description": description,
                }
                if self.options.search_terms:
                    matches = True
                    for option in self.options.search_terms:
                        if option.lower() not in str(row).lower():
                            matches = False
                            break
                    if not matches:
                        continue
                if self.options.having:
                    if not evaluate_expression(self.options.having, row, functions):
                        continue

                table.add_row(row["name"], row["description"])

            self.console.print(table)
