import argparse

from rich.table import Table

from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Searches Jira for fields matching your search query."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--search-term",
            help="A partial string to match against your search field's name or key.",
        )

    def handle(self) -> None:
        table = Table(title="Matching Fields")
        table.add_column(header="key", style="cyan")
        table.add_column(header="type", style="green")
        table.add_column(header="name", style="bright_cyan")

        search_term = ""
        if self.options.search_term:
            search_term = self.options.search_term.lower()

        fields = sorted(self.jira.fields(), key=lambda field: field["name"])
        for field in fields:
            if (
                search_term not in field["key"].lower()
                and search_term not in field["name"].lower()
            ):
                continue

            table.add_row(
                field["key"], field.get("schema", {}).get("type", ""), field["name"]
            )

        self.console.print(table)
