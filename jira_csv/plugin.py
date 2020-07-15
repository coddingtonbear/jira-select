from __future__ import annotations

from abc import ABCMeta, abstractmethod
import argparse
import logging
from typing import Any, Dict, Optional, Type
import pkg_resources

from PyInquirer import prompt
from jira import JIRA
import keyring
from rich.console import Console

from .constants import APP_NAME
from .exceptions import ConfigurationError
from .types import ConfigDict, Question
from .utils import save_config


logger = logging.getLogger(__name__)


def get_installed_commands() -> Dict[str, Type[BaseCommand]]:
    possible_commands: Dict[str, Type[BaseCommand]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="jira_csv_commands"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseCommand):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jira_csv.plugin.BaseCommand`.",
                entry_point,
            )
            continue
        possible_commands[entry_point.name] = loaded_class

    return possible_commands


class BaseCommand(metaclass=ABCMeta):
    _jira: Optional[JIRA] = None

    def __init__(self, config: ConfigDict, options: argparse.Namespace):
        self._config: ConfigDict = config
        self._options: argparse.Namespace = options
        self._console = Console()
        super().__init__()

    @property
    def config(self) -> ConfigDict:
        return self._config

    def save_config(self) -> None:
        save_config(self.config, self.options.config)

    @property
    def options(self) -> argparse.Namespace:
        return self._options

    @property
    def console(self) -> Console:
        return self._console

    def prompt(self, question: Question) -> Any:
        question["name"] = "question"

        return prompt([question]).get("question", None)

    @property
    def jira(self) -> JIRA:
        if self._jira is None:
            instance_url = self.config.get("instance_url") or self.options.instance_url
            if not instance_url:
                raise ConfigurationError("instance_url not set")

            username = self.config.get("username") or self.options.username
            if not username:
                raise ConfigurationError("username not set")

            password = self.config.get("password") or self.options.password
            if not password:
                password = keyring.get_password(APP_NAME, instance_url + username)
                if not password:
                    raise ConfigurationError(
                        f"Password not stored for {instance_url} user {username}; "
                        f"use the 'store-password' command to store the password "
                        f"for this user account in your system keyring."
                    )
            self._jira = JIRA(
                server=instance_url,
                options={"agile_rest_path": "agile",},
                basic_auth=(username, password),
            )

        return self._jira

    @classmethod
    def get_help(cls) -> str:
        return ""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        pass

    @abstractmethod
    def handle(self) -> None:
        pass
