import argparse
import getpass

import keyring

from ..constants import APP_NAME
from ..exceptions import UserError
from ..plugin import BaseCommand
from ..types import InstanceDefinition


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Stores the password for a given user account in your system keychain."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("username")

    def handle(self):
        password = getpass.getpass("Password: ")

        if not password:
            raise UserError("Password required")

        instance = self.config.instances.get(
            self.options.instance_name, InstanceDefinition()
        )

        instance_url = self.options.instance_url or instance.url
        keyring.set_password(APP_NAME, instance_url + self.options.username, password)
