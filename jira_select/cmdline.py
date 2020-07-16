import argparse

from rich.traceback import install as enable_rich_traceback

from .plugin import get_installed_commands
from .utils import get_config


def main():
    enable_rich_traceback()
    commands = get_installed_commands()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        type=str,
        help="Path to configuration file to load.",
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
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    for cmd_name, cmd_class in commands.items():
        parser_kwargs = {}

        cmd_help = cmd_class.get_help()
        if cmd_help:
            parser_kwargs["help"] = cmd_help

        subparser = subparsers.add_parser(cmd_name, **parser_kwargs)
        cmd_class.add_arguments(subparser)

    args = parser.parse_args()

    config = get_config(path=args.config)

    command = commands[args.command](config=config, options=args)
    command.handle()
