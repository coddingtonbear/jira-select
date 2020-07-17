import argparse
import sys
from typing import IO

from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog
from yaml import safe_dump

from ..exceptions import UserError
from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Interactively generates a query definition (in yaml format)."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--output",
            "-o",
            help="Path to file where records will be written; default: stdout.",
        )

    def get_select_fields(self):
        return checkboxlist_dialog(
            title="Select",
            text="Which fields would you like to select in your query?",
            values=[
                (
                    f'{field["id"]} as "{field["name"]}"',
                    f'{field["name"]} ({field["id"]})',
                )
                for field in sorted(self.jira.fields(), key=lambda x: x["name"])
            ],
        ).run()

    def get_where(self):
        return input_dialog(
            title="Where",
            text="(Optional) Enter a JQL query for limiting your search results.",
        ).run()

    def handle(self) -> None:
        fields = self.get_select_fields()
        if not fields:
            raise UserError("No fields selected")

        where = self.get_where()
        if not where:
            where = None

        output: IO[str] = sys.stdout
        if self.options.output:
            output = open(self.options.output, "w")

        query = {"select": fields, "from": "issues"}

        if where:
            query["where"] = [where]

        safe_dump(query, output)

        if output is not sys.stdout:
            output.close()
