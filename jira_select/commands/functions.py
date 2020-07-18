import argparse
import inspect

from rich.table import Table

from ..plugin import BaseCommand, get_installed_functions
from ..utils import evaluate_expression


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Lists all available functions, their signatures, and description."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--having",
            help=(
                "A 'having' expression to use for limiting the displayed results. "
                "Searchable fields are 'name' and 'description'. "
                "E.g.--having=\"'average' in description.lower()\". "
            ),
        )

    def handle(self):
        table = Table(title="functions")
        table.add_column(header="name", style="green")
        table.add_column(header="description", style="white")

        functions = get_installed_functions(self.jira)
        for name, fn in functions.items():
            docstring = fn.__doc__

            try:
                signature = (
                    f"[bright_cyan]{name}{inspect.signature(fn)}[/bright_cyan]\n\n"
                )
            except Exception:
                signature = ""

            description = signature + docstring.strip() + "\n\n"

            if self.options.having:
                row = {
                    "name": name,
                    "description": description,
                }
                if not evaluate_expression(self.options.having, row, functions):
                    continue

            table.add_row(name, description)

        self.console.print(table)
