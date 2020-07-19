import argparse
import os
import tempfile
import subprocess
from typing import cast

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.data import YamlLexer
from yaml import safe_load

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
        query = Query(self.jira, query_definition, progress_bar=True)
        with tempfile.NamedTemporaryFile("w", suffix=".csv") as outf:
            with CsvFormatter(query, outf) as formatter:
                for row in query:
                    formatter.writerow(row)
            outf.flush()

            proc = subprocess.Popen([viewer, outf.name])
            proc.wait()

    def build_completions(self) -> WordCompleter:
        function_completions = get_installed_functions(self.jira).keys()
        field_completions = [field["key"] for field in self.jira.fields()]

        return WordCompleter(function_completions | field_completions)

    def handle(self) -> None:
        vi_mode = bool(
            self.options.editor_mode == "vi"
            or self.config.get("shell", {}).get("vi_mode", False)
        )

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
