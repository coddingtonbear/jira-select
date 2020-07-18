import argparse

import keyring
from prompt_toolkit.shortcuts import input_dialog

from ..constants import APP_NAME
from ..exceptions import UserError
from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Stores the password for a given user account in your system keychain."

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("username")

    def handle(self):
        password = input_dialog(
            title="Password",
            text=f"Password for {self.options.username}: ",
            password=True,
        ).run()

        if not password:
            raise UserError("Password required")

        instance_url = self.config.get("instance_url") or self.options.instance_url
        keyring.set_password(APP_NAME, instance_url + self.options.username, password)
