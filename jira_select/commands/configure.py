from logging import getLogger
from typing import Tuple

import keyring
from jira import JIRA, JIRAError
from prompt_toolkit.shortcuts import input_dialog, yes_no_dialog

from ..constants import APP_NAME
from ..exceptions import UserError
from ..plugin import BaseCommand

logger = getLogger(__name__)


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Interactively allows you to configure jira-csv to connect "
            "to your Jira instance."
        )

    def collect_credentials(self) -> Tuple[str, str, str]:
        instance_url = input_dialog(
            title="Instance URL",
            text="Jira instance URL (example: 'https://mycompany.jira.com/')",
        ).run()
        import pdb

        pdb.set_trace()
        username = input_dialog(title="Username", text="Username").run()
        password = input_dialog(
            title="Password", text=f"Password for {username}: ", password=True
        ).run()

        return instance_url, username, password

    def handle(self) -> None:
        instance_url = ""
        username = ""
        password = ""

        while True:
            instance_url, username, password = self.collect_credentials()

            try:
                JIRA(
                    instance_url,
                    options={"agile_rest_path": "agile",},
                    basic_auth=(username, password),
                    max_retries=0,
                )
                break
            except JIRAError:
                result = yes_no_dialog(
                    title="Error connecting to Jira",
                    text=(
                        "A connection to Jira could not be established using "
                        "the credentials you provided; try again?"
                    ),
                ).run()
                if not result:
                    raise UserError("Aborted; configuration not saved.")

        self.config.update({"instance_url": instance_url, "username": username})

        self.save_config()

        store_password = yes_no_dialog(
            title="Save password?",
            text="Would you like to save this password to your system keyring?",
        ).run()
        if store_password:
            keyring.set_password(APP_NAME, instance_url + username, password)
