import argparse
import os
import tempfile
import subprocess
from typing import cast

from jira import JIRAError
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.data import YamlLexer
from yaml import safe_load

from ..exceptions import QueryError
from ..formatters.csv import Formatter as CsvFormatter
from ..plugin import BaseCommand, get_installed_functions
from ..query import Query
from ..types import QueryDefinition
from ..utils import get_config_dir


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
            "--editor-mode", "-m", choices=["emacs", "vi"], default=None,
        )

    def _prompt_loop(self, session: PromptSession):
        viewer: str = cast(str, self.config.get("viewers", {}).get("csv")) or "vd"

        result = session.prompt("Query > ")

        query_definition: QueryDefinition = safe_load(result)
        try:
            query = Query(self.jira, query_definition, progress_bar=True)
        except Exception:
            self.console.print("[red]Your query could not be parsed[/red]")
            return

        try:
            with tempfile.NamedTemporaryFile("w", suffix=".csv") as outf:
                with CsvFormatter(query, outf) as formatter:
                    for row in query:
                        formatter.writerow(row)
                outf.flush()

                proc = subprocess.Popen([viewer, outf.name])
                proc.wait()
        except JIRAError as e:
            self.console.print(f"[red][bold]Jira Error:[/bold] {e.text}[/red]")
        except QueryError as e:
            self.console.print(f"[red][bold]Query Error:[/bold] {e}[/red]")
        except Exception:
            self.console.print_exception()

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
        ]
        function_completions = list(get_installed_functions(self.jira).keys())
        field_completions = [field["id"] for field in self.jira.fields()]

        return WordCompleter(sql_completions + function_completions + field_completions)

    def handle(self) -> None:
        vi_mode = not self.config.get("shell", {}).get("emacs_mode", False)
        if self.options.editor_mode:
            vi_mode = self.options.editor_mode

        completions = self.build_completions()
        session = PromptSession(
            lexer=PygmentsLexer(YamlLexer),
            multiline=True,
            completer=completions,
            complete_while_typing=False,
            history=FileHistory(os.path.join(get_config_dir(), "shell_history")),
            auto_suggest=AutoSuggestFromHistory(),
            vi_mode=vi_mode,
        )

        while True:
            try:
                self._prompt_loop(session)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
