import argparse
import importlib.util
import os
import sys
import tempfile

from ..exceptions import UserError
from ..plugin import BaseCommand
from ..utils import get_custom_function_dir


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        path = get_custom_function_dir()
        return (
            "Installs a user script (i.e. a python script having functions "
            "decorated with `jira_select.plugin.register_function`) into "
            f"your user configuration directory at {path}."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "python_script",
            type=argparse.FileType("r"),
            help=("Script to install into your user scripts directory."),
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help=(
                "By default, if the specified filename matches an existing "
                "user script, an exception will be raised. If you would like "
                "to overwrite an existing file, though, you can use this "
                "argument."
            ),
        )
        parser.add_argument(
            "--name",
            default=None,
            help=(
                "Override the name of your generated script; if not named "
                "ending with `.py`, `.py` will be appended automatically."
            ),
        )
        return super().add_arguments(parser)

    def handle(self, *args, **kwargs) -> None:
        name = self.options.name
        if name is None and self.options.python_script is not sys.stdin:
            name = self.options.python_script.name
        if name is None:
            raise UserError(
                "When creating a script file from stdin, you must "
                "provide the --name command-line argument."
            )
        if not name.endswith(".py"):
            name += ".py"

        full_path = os.path.join(get_custom_function_dir(), name)
        if not self.options.overwrite and os.path.exists(full_path):
            raise UserError(
                f"Path {full_path} already exists; use --overwrite to overwrite."
            )

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as tmpf:
            tmpf.write(self.options.python_script.read())
            tmpf.flush()
            tmpf.seek(0)

            try:
                spec = importlib.util.spec_from_file_location(
                    "temporary_user_script", tmpf.name
                )
                assert spec
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)  # type: ignore
            except Exception as e:
                raise UserError(f"Could not install user script: {e}")

            tmpf.seek(0)
            with open(full_path, "w") as outf:
                outf.write(tmpf.read())
