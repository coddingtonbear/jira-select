import argparse
import json

from rich.table import Table

from ..plugin import BaseCommand
from ..utils import JiraSelectJsonEncoder


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Displays Jira instances that you have configured jira-select "
            "to be able to use."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--json",
            "-j",
            default=False,
            action="store_true",
            help="Export schema as JSON format instead of printing a table.",
        )

    def handle(self) -> None:
        if self.options.json:
            instances = []
            for instance_name, instance_data in self.config.instances.items():
                instances.append(
                    {
                        "name": instance_name,
                        "username": instance_data.username,
                        "url": instance_data.url,
                    }
                )
            self.console.print(
                json.dumps(
                    instances, cls=JiraSelectJsonEncoder, sort_keys=True, indent=4
                )
            )
        else:
            table = Table(title="Configured Instances")
            table.add_column("name", style="green")
            table.add_column("username", style="cyan")
            table.add_column("url", style="bright_cyan")

            for instance_name, instance_data in self.config.instances.items():
                table.add_row(instance_name, instance_data.username, instance_data.url)

            self.console.print(table)
