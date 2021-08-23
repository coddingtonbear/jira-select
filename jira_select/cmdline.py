import argparse
import logging

from rich.console import Console
from rich.traceback import install as enable_rich_traceback
from safdie import SafdieRunner

from .constants import COMMAND_ENTRYPOINT
from .exceptions import UserError
from .plugin import BaseCommand
from .utils import get_config
from .utils import get_default_config_path


def main():
    enable_rich_traceback()

    default_config_path = get_default_config_path()

    parser = argparse.ArgumentParser()
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
            "Print logging messages of the specified level and above " "to the console."
        ),
    )
    runner = SafdieRunner(COMMAND_ENTRYPOINT, cmd_class=BaseCommand, parser=parser)
    args = runner.parse_args()

    if args.log_level:
        logging.basicConfig(level=logging.getLevelName(args.log_level))

    if args.debugger:
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))

        # Pause the program until a remote debugger is attached
        debugpy.wait_for_client()

    config = get_config(path=args.config)

    console = Console()

    try:
        runner.run_command_for_parsed_args(args, init_kwargs={"config": config})
    except UserError as e:
        console.print(f"[red]{e}[/red]")
    except Exception:
        console.print_exception()
