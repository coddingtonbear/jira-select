import argparse
import subprocess
import sys
from typing import Optional
from typing import Tuple

from yaml import safe_load

from jira_select.exceptions import UserError
from jira_select.utils import launch_default_viewer

from ..constants import DEFAULT_INLINE_VIEWERS
from ..plugin import BaseCommand
from ..plugin import get_installed_formatters
from ..query import Executor
from ..types import QueryDefinition


def parameter_tuple(value: str) -> Tuple[str, str]:
    return tuple(value.split("=", 1))  # type: ignore


class Command(BaseCommand):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        formatters = get_installed_formatters()

        parser.add_argument(
            "query_file",
            nargs="?",
            type=argparse.FileType("r"),
            default=sys.stdin,
            help="Query definition file to run",
        )
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
            type=argparse.FileType("wb+"),
            default=sys.stdout.buffer,
            help="Path to file where records will be written; default: stdout.",
        )
        parser.add_argument(
            "--launch-default-viewer",
            "-l",
            action="store_true",
            default=False,
            help=(
                "Display the output using the default viewer for the "
                "filetype used by the selected formatter instead of "
                "displaying the results inline."
            ),
            dest="launch_default_viewer",
        )
        parser.add_argument(
            "--view",
            "-v",
            default=False,
            action="store_true",
            help="Launch viewer immediately after completing query.",
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

    @classmethod
    def get_help(cls) -> str:
        return "Runs a query definition specified in yaml format."

    def handle(self) -> None:
        if self.options.view and self.options.output is sys.stdout:
            raise UserError("Must specify --output to use --view.")

        viewer: Optional[str] = self.config.inline_viewers.get(
            self.options.format, DEFAULT_INLINE_VIEWERS.get(self.options.format)
        )

        formatter_cls = get_installed_formatters()[self.options.format]

        query_definition: QueryDefinition
        query_definition = QueryDefinition.parse_obj(safe_load(self.options.query_file))

        query = Executor(
            self.jira,
            query_definition,
            progress_bar=(self.options.output is not sys.stdout.buffer)
            if self.options.progressbar
            else False,
            parameters=dict(self.options.parameters or []),
            enable_cache=self.options.cache,
        )
        with formatter_cls(query, self.options.output) as formatter:
            for row in query:
                formatter.writerow(row)
                self.options.output.flush()

        if self.options.view and self.options.launch_default_viewer:
            launch_default_viewer(self.options.output.name)
        elif self.options.view:
            if viewer:
                proc = subprocess.Popen([viewer, self.options.output.name])
                proc.wait()
            else:
                self.options.output.seek(0)
                self.console.print(self.options.output.read().decode("utf-8"))
