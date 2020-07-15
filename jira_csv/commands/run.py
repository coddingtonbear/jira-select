import argparse
import subprocess
import tempfile
import sys
from typing import IO

from yaml import safe_load

from ..plugin import BaseCommand
from ..query import Query
from ..types import QueryDefinition


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("query_file", help="Query definition file to run")
        parser.add_argument("--output", "-o")
        parser.add_argument("--view", "-v", default=False, action="store_true")

    @classmethod
    def get_help(cls) -> str:
        return "Interactively generates a query definition (in yaml format)."

    def handle(self) -> None:
        query_definition: QueryDefinition = {}
        with open(self.options.query_file, "r") as inf:
            query_definition = safe_load(inf)

        output: IO[str] = sys.stdout
        output_file = self.options.output
        needs_close = False
        if self.options.output:
            output = open(self.options.output, "w")
            needs_close = True
        elif self.options.view:
            output = tempfile.NamedTemporaryFile("w", suffix=".csv")
            output_file = output.name
            needs_close = True

        query = Query(self.jira, query_definition)
        query.write_csv(output)
        output.flush()

        if self.options.view:
            viewer = self.config.get("viewer", "vd")

            proc = subprocess.Popen([viewer, output_file])
            proc.wait()

        if needs_close:
            output.close()
