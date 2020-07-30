import argparse
import importlib.machinery

from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Runs the 'main(**kwargs)' function in the specified file; "
            "see documentation for details."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "file_path",
            type=str,
            help=(
                "Path to the file containg the `main(**kwargs)` function" "to execute."
            ),
        )
        parser.add_argument("command_args", nargs=argparse.REMAINDER)

    def handle(self):
        run_script_module = importlib.machinery.SourceFileLoader(
            "run_script", self.options.file_path
        ).load_module()
        run_script_module.main(args=self.options.command_args, cmd=self)
