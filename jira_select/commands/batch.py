import argparse
import copy
import sys
from csv import DictReader
from csv import DictWriter
from typing import List
from typing import Tuple

from yaml import safe_load

from jira_select.exceptions import UserError

from ..plugin import BaseCommand
from ..query import Executor
from ..types import QueryDefinition
from ..types import SelectFieldDefinition
from ..utils import parse_select_definition


def parameter_tuple(value: str) -> Tuple[str, str]:
    return tuple(value.split("=", 1))  # type: ignore


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Runs a specified Jira-select query multiple times with params and values specified by a CSV file."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)

        parser.add_argument(
            "query_file",
            type=argparse.FileType("r"),
            help="Query definition file to run",
        )
        parser.add_argument(
            "csv_file",
            nargs="?",
            type=argparse.FileType("r"),
            help="CSV File having parameters as headers and rows as values to use as parameters.",
            default=sys.stdin,
        )
        parser.add_argument(
            "--output",
            "-o",
            type=argparse.FileType("w"),
            default=sys.stdout,
            help="Path to file where records will be written; default: stdout.",
        )
        parser.add_argument(
            "--param",
            "-p",
            dest="parameters",
            action="append",
            type=parameter_tuple,
        )
        parser.add_argument(
            "--no-cache",
            "-c",
            default=True,
            action="store_false",
            help="Do not use cached data.",
            dest="cache",
        )
        parser.add_argument(
            "--disable-progressbars",
            "-b",
            default=True,
            action="store_false",
            help="",
            dest="progressbar",
        )

    def get_select_fields(self, select) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        if isinstance(select, str):
            fields.append(parse_select_definition(select))
        if isinstance(select, dict):
            for column, expression in select.items():
                fields.append(
                    SelectFieldDefinition(
                        expression=expression if expression else column, column=column
                    )
                )
        elif isinstance(select, list):
            for field in select:
                fields.append(parse_select_definition(field))

        return fields

    def handle(self) -> None:
        query_definition: QueryDefinition
        query_definition = QueryDefinition.parse_obj(safe_load(self.options.query_file))

        reader = DictReader(self.options.csv_file)

        if reader.fieldnames is None:
            raise UserError("Incoming CSV file defines no parameters")

        writer = DictWriter(
            self.options.output,
            fieldnames=(
                list(reader.fieldnames)
                + [f.column for f in self.get_select_fields(query_definition.select)]
            ),
        )
        writer.writeheader()

        for input_row in reader:
            params = copy.copy(input_row)
            params.update(dict(self.options.parameters or []))

            query = Executor(
                self.jira,
                query_definition,
                progress_bar=(
                    (self.options.output is not sys.stdout)
                    if self.options.progressbar
                    else False
                ),
                parameters=params,
                enable_cache=self.options.cache,
            )
            query_rows = list(query)

            had_results = False
            for result_row in query_rows:
                output_row = copy.copy(input_row)
                output_row.update(result_row)

                writer.writerow(output_row)
                had_results = True

            if not had_results:
                writer.writerow(input_row)
