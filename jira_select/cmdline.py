import argparse
import logging
import sys
from typing import Any
from typing import Dict
from typing import Iterable

from rich.console import Console
from rich.logging import RichHandler
from safdie import SafdieRunner

from .constants import COMMAND_ENTRYPOINT
from .exceptions import UserError
from .plugin import BaseCommand
from .utils import get_config
from .utils import get_default_config_path


class Runner(SafdieRunner):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        default_config_path = get_default_config_path()
        parser.add_argument(
            "--config",
            "-c",
            default=default_config_path,
            type=str,
            help=(
                "Path to configuration file to load; by default configuration "
                f"will be loaded from {default_config_path}."
            ),
        )
        parser.add_argument(
            "--instance-name",
            "-n",
            default="default",
            help=(
                "Named instance to connect to.  You can define new instances by "
                'running `jira-select configure --instance-name="my-instance"` '
                "to set the instance URL, username, and password for later use in "
                'other commands via providing the `--instance-name="my-instance" '
                "command-line argument.  By default the 'default' instance name "
                "will be used."
            ),
        )
        parser.add_argument(
            "--instance-url",
            "-i",
            default=None,
            type=str,
            help="URL of the Jira instance to connect to (if you cannot use 'configure')",
        )
        parser.add_argument(
            "--username",
            "-u",
            default=None,
            type=str,
            help="Username to use for connecting to Jira (if you cannot use 'configure')",
        )
        parser.add_argument(
            "--password",
            "-p",
            default=None,
            type=str,
            help=(
                "Password to use for connecting to Jira.  NOT RECOMMENDED: use the "
                "'store-password' or 'configure' command instead."
            ),
        )
        parser.add_argument(
            "--certificate",
            help=(
                "Path to a certificate to self-signed certificate use for "
                "connecting to your instance."
            ),
        )
        parser.add_argument(
            "--disable-certificate-verification",
            action="store_true",
            default=False,
            help="Do not verify server certificate.  Generally not recommended.",
        )
        parser.add_argument(
            "--debugger",
            action="store_true",
            help=(
                "Wait for debugger connection before processing command (requires debugpy)."
            ),
        )
        parser.add_argument(
            "--log-level",
            help=(
                "Print logging messages of the specified level and above "
                "to the console."
            ),
            default="INFO",
        )
        return super().add_arguments(parser)

    def handle(
        self,
        args: argparse.Namespace,
        init_args: Iterable[Any],
        init_kwargs: Dict[str, Any],
        handle_args: Iterable[Any],
        handle_kwargs: Dict[str, Any],
    ) -> Any:
        console = Console()
        logging.basicConfig(
            level=logging.getLevelName(args.log_level),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, console=Console(stderr=True))],
        )

        if args.debugger:
            import debugpy

            debugger_host = "0.0.0.0"
            debugger_port = 5678

            debugpy.listen((debugger_host, debugger_port))

            console.print(
                f"[magenta]Waiting for debugger connection on {debugger_host}:{debugger_port}[/magenta]..."
            )

            # Pause the program until a remote debugger is attached
            debugpy.wait_for_client()

        config = get_config(path=args.config)

        init_kwargs["config"] = config
        return super().handle(args, init_args, init_kwargs, handle_args, handle_kwargs)


def main():
    console = Console()

    try:
        Runner(COMMAND_ENTRYPOINT, cmd_class=BaseCommand).run()
    except UserError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception:
        console.print_exception()
        sys.exit(1)
