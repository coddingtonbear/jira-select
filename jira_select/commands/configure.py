from logging import getLogger
from typing import Optional
from urllib.parse import urlparse

import keyring
from jira import JIRA, JIRAError

from ..constants import APP_NAME
from ..exceptions import UserError
from ..plugin import BaseCommand

logger = getLogger(__name__)


def validate_url(url: Optional[str]) -> bool:
    if url is None:
        return False

    parsed = urlparse(url)

    return bool(parsed.scheme and parsed.netloc)


def require(data: Optional[str]) -> bool:
    if not data:
        return False

    return True


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Interactively allows you to configure jira-csv to connect "
            "to your Jira instance."
        )

    def handle(self) -> None:
        instance_url = self.prompt(
            {
                "type": "input",
                "message": "Jira instance URL (example: 'https://mycompany.jira.com/')",
                "validate": validate_url,
            }
        )
        username = self.prompt(
            {"type": "input", "message": "Username", "validate": require}
        )
        password = self.prompt(
            {
                "type": "password",
                "message": f"Password for {username}",
                "validate": require,
            }
        )

        logger.info("Connected to Jira successfully; configuration updated.")

        try:
            JIRA(
                instance_url,
                options={"agile_rest_path": "agile",},
                basic_auth=(username, password),
                max_retries=0,
            )
        except JIRAError:
            raise UserError("Could not connect to Jira using the provided credentials")

        self.config.update({"instance_url": instance_url, "username": username})

        logger.info("Connected to Jira successfully; configuration updated.")

        self.save_config()

        store_password = self.prompt(
            {"type": "confirm", "message": "Store password in keyring?"}
        )
        if store_password:
            keyring.set_password(APP_NAME, instance_url + username, password)
