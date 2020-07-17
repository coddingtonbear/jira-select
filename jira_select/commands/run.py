import argparse
import subprocess
import sys
import tempfile
from typing import IO, Dict, Optional, cast

from rich.progress import track
from yaml import safe_load

from ..exceptions import UserError
from ..plugin import BaseCommand, get_installed_formatters
from ..query import Query
from ..types import QueryDefinition


class Command(BaseCommand):
    DEFAULT_VIEWERS: Dict[str, str] = {"csv": "vd"}

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        formatters = get_installed_formatters()

        parser.add_argument("query_file", help="Query definition file to run")
        parser.add_argument(
            "--format",
            "-f",
            choices=formatters.keys(),
            default="csv",
            help="Data format in which to write record data; default: 'csv'.",
        )
        parser.add_argument(
            "--output",
            "-o",
            help="Path to file where records will be written; default: stdout.",
        )
        parser.add_argument(
            "--view",
            "-v",
            default=False,
            action="store_true",
            help="Launch viewer immediately after completing query.",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Interactively generates a query definition (in yaml format)."

    def handle(self) -> None:
        viewer: Optional[str] = cast(
            str, self.config.get("viewers", {}).get(self.options.format)
        ) or self.DEFAULT_VIEWERS.get(self.options.format)
        if not viewer and self.options.view:
            raise UserError(f"No viewer set for format {self.options.format}")
        formatter_cls = get_installed_formatters()[self.options.format]

        query_definition: QueryDefinition = {}
        with open(self.options.query_file, "r") as inf:
            query_definition = safe_load(inf)

        output: IO[str] = sys.stdout
        output_file = self.options.output
        if self.options.output:
            output = open(self.options.output, "w")
        elif self.options.view:
            output = tempfile.NamedTemporaryFile(
                "w", suffix=f".{formatter_cls.get_file_extension()}"
            )
            output_file = output.name

        query = Query(self.jira, query_definition, emit_omissions=True)
        with formatter_cls(query, output) as formatter:
            if output == sys.stdout:
                for row in query:
                    if row is not None:
                        formatter.writerow(row)
            else:
                count = query.count()
                for row in track(query, description="Running query...", total=count):
                    if row is not None:
                        formatter.writerow(row)
        output.flush()

        if self.options.view:
            assert viewer

            proc = subprocess.Popen([viewer, output_file])
            proc.wait()

        if output is not sys.stdout:
            output.close()
