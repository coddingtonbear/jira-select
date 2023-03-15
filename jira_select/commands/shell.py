import argparse
import os
import shutil
import subprocess
import tempfile
from typing import IO
from typing import Optional
from typing import Type

from jira import JIRAError
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.data import YamlLexer
from yaml import safe_load

from .. import __version__
from ..constants import DEFAULT_INLINE_VIEWERS
from ..exceptions import QueryError
from ..plugin import BaseCommand
from ..plugin import BaseFormatter
from ..plugin import get_installed_formatters
from ..plugin import get_installed_functions
from ..query import Executor
from ..types import QueryDefinition
from ..utils import get_config_dir
from ..utils import launch_default_viewer


class QueryParseError(Exception):
    pass


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Opens an interactive shell (a.k.a. repl) allowing you to "
            "interact with Jira and see results immediately (like "
            "the sqlite3, postgres, or mysql shells)."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--editor-mode",
            "-m",
            choices=["emacs", "vi"],
            default=None,
        )
        parser.add_argument(
            "--disable-progressbars",
            "-b",
            action="store_false",
            default=True,
            dest="enable_progressbars",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=argparse.FileType("wb+"),
            default=None,
            help=(
                "Path to file where records will be written; default: "
                "a temporary file."
            ),
        )
        parser.add_argument(
            "--launch-default-viewer",
            "-l",
            action="store_true",
            default=False,
            help=(
                "Display the output using the default viewer for the "
                "filetype used by the selected formatter instead of "
                "displaying the results inline.  Depending upon your "
                "operating system, you may need to explicitly specify "
                "the output file path using the --output parameter "
                "for this option to work."
            ),
            dest="launch_default_viewer",
        )
        parser.add_argument(
            "--format",
            "-f",
            default="json",
            choices=get_installed_formatters().keys(),
            dest="format",
        )

    def _prompt_loop(
        self,
        session: PromptSession,
        formatter_cls: Type[BaseFormatter],
        outf: IO[bytes],
    ):
        result = session.prompt(">>> ")

        try:
            query_definition: QueryDefinition = QueryDefinition.parse_obj(
                safe_load(result)
            )
            query = Executor(
                self.jira,
                query_definition,
                progress_bar=self.options.enable_progressbars,
            )
        except Exception as e:
            raise QueryParseError(e)

        outf.seek(0)
        outf.truncate()

        with formatter_cls(query, outf) as formatter:
            for row in query:
                formatter.writerow(row)
                outf.flush()

        if self.options.launch_default_viewer:
            launch_default_viewer(outf.name)
        else:
            self._inline_viewer(outf)

    def _inline_viewer(self, fobj: IO[bytes]):
        viewer: Optional[str] = self.config.inline_viewers.get(
            self.options.format, DEFAULT_INLINE_VIEWERS.get(self.options.format)
        )

        if viewer and shutil.which(viewer):
            proc = subprocess.Popen([viewer, fobj.name])
            proc.wait()
        else:
            fobj.seek(0)
            self.console.print(fobj.read().decode("utf-8"))

    def build_completions(self) -> WordCompleter:
        sql_completions = [
            "select",
            "from",
            "where",
            "order_by",
            "having",
            "group_by",
            "sort_by",
            "expand",
            "limit",
            "cap",
        ]
        function_completions = list(get_installed_functions(self.jira).keys())
        field_completions = [field["id"] for field in self.jira.fields()]

        return WordCompleter(sql_completions + function_completions + field_completions)

    def handle(self) -> None:
        self.console.print(
            f"[bold]Jira-select[/bold] Shell v{__version__}",
            style="dodger_blue1 blink",
        )
        vi_mode = not self.config.shell.emacs_mode
        if self.options.editor_mode:
            vi_mode = self.options.editor_mode
        if vi_mode:
            self.console.print(
                " | [bold]Run:[/bold]\t\tESC->ENTER",
                style="deep_sky_blue4",
            )
            self.console.print(
                " | [bold]Clear:[/bold]\tCTRL+C",
                style="deep_sky_blue4",
            )
            self.console.print(
                " | [bold]Exit:[/bold]\tCTRL+D",
                style="deep_sky_blue4",
            )

        completions = self.build_completions()
        session: PromptSession = PromptSession(
            lexer=PygmentsLexer(YamlLexer),
            multiline=True,
            completer=completions,
            complete_while_typing=False,
            history=FileHistory(os.path.join(get_config_dir(), "shell_history")),
            auto_suggest=AutoSuggestFromHistory(),
            vi_mode=vi_mode,
            mouse_support=True,
        )
        formatter_cls = get_installed_formatters()[self.options.format]

        output = self.options.output
        if not output:
            output = tempfile.NamedTemporaryFile(
                "wb+",
                suffix=f".{formatter_cls.get_file_extension()}",
            )

        while True:
            try:
                self._prompt_loop(session, formatter_cls, output)
            except JIRAError as e:
                self.console.print(f"[red][bold]Jira Error:[/bold] {e.text}[/red]")
            except QueryError as e:
                self.console.print(f"[red][bold]Query Error:[/bold] {e}[/red]")
            except QueryParseError as e:
                self.console.print(
                    f"[red][bold]Parse Error:[/bold] Your query could not be parsed: {e}[/red]"
                )
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception:
                self.console.print_exception()

        output.close()
