import argparse
import sys
from typing import Any
from typing import Dict
from typing import Union

import keyring
from jira import JIRA
from jira import JIRAError
from urllib3 import disable_warnings

from jira_select.types import InstanceDefinition

from ..constants import APP_NAME
from ..exceptions import UserError
from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Set up a Jira instance using command-line arguments.  "
            "Note: if you are a human, you probably want to use "
            "`configure` instead.  If `--password` is not specified "
            "as an argument, password will be read from stdin."
        )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--no-verify",
            "-n",
            help="Do not attempt to verify the provided credentials before saving.",
        )
        return super().add_arguments(parser)

    def handle(self, *args, **kwargs) -> None:
        verify: Union[bool, str] = True
        if self.options.disable_certificate_verification:
            verify = False
        elif self.options.certificate:
            verify = self.options.certificate

        password = self.options.password
        if not password:
            password = sys.stdin.read()

        if (
            not password
            or not self.options.instance_name
            or not self.options.username
            or not self.options.instance_url
        ):
            raise UserError(
                "Missing parameter; password, instance_name, username, "
                "and instance_url are all required."
            )

        if not self.options.no_verify:
            try:
                if self.options.disable_certificate_verification:
                    disable_warnings()

                options: Dict[str, Any] = {
                    "agile_rest_path": "agile",
                    "server": self.options.instance_url,
                    "verify": verify,
                }
                JIRA(
                    options,
                    basic_auth=(self.options.username, password),
                    max_retries=0,
                )
            except JIRAError as e:
                raise UserError(e)

        self.config.instances[self.options.instance_name] = InstanceDefinition(
            url=self.options.instance_url, username=self.options.username, verify=verify
        )
        self.save_config()

        keyring.set_password(
            APP_NAME,
            self.options.instance_url + self.options.username,
            password,
        )
