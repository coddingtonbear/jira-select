from __future__ import annotations

import argparse
import logging
from abc import ABCMeta, abstractmethod
from typing import IO, TYPE_CHECKING, Any, Callable, Dict, Optional, Type, cast

import pkg_resources

import keyring
from jira import JIRA
from rich.console import Console

from .constants import APP_NAME
from .exceptions import ConfigurationError
from .types import ConfigDict
from .utils import save_config

if TYPE_CHECKING:
    from .query import Query

logger = logging.getLogger(__name__)


def get_installed_commands() -> Dict[str, Type[BaseCommand]]:
    possible_commands: Dict[str, Type[BaseCommand]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="jira_select.commands"):
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
                "not a subclass of `jira_select.plugin.BaseCommand`.",
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
        ...


def get_installed_formatters() -> Dict[str, Type[BaseFormatter]]:
    possible_formatters: Dict[str, Type[BaseFormatter]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="jira_select.formatters"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseFormatter):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jira_select.plugin.BaseFormatter`.",
                entry_point,
            )
            continue
        possible_formatters[entry_point.name] = loaded_class

    return possible_formatters


class BaseFormatter(metaclass=ABCMeta):
    def __init__(self, query: Query, stream: IO[str]):
        self._query = query
        self._stream = stream

    @classmethod
    @abstractmethod
    def get_file_extension(cls) -> str:
        ...

    @property
    def query(self):
        return self._query

    @property
    def stream(self):
        return self._stream

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        # Exception handling here
        self.close()

    def open(self):
        return

    def close(self):
        return

    @abstractmethod
    def writerow(self, row: Dict[str, Any]):
        ...


def get_installed_functions(jira: JIRA = None) -> Dict[str, Callable]:
    possible_commands: Dict[str, BaseFunction] = {}
    for entry_point in pkg_resources.iter_entry_points(group="jira_select.functions"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseFunction):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jira_select.plugin.BaseFunction`.",
                entry_point,
            )
            continue
        possible_commands[entry_point.name] = loaded_class(jira)

    return cast(Dict[str, Callable], possible_commands)


class BaseFunction(metaclass=ABCMeta):
    def __init__(self, jira: Optional[JIRA]):
        self._jira = jira

    @property
    def jira(self):
        assert self._jira

        return self._jira

    @abstractmethod
    def process(self, *args, **kwargs) -> Optional[Any]:
        ...

    def __call__(self, *args, **kwargs) -> Optional[Any]:
        return self.process(*args, **kwargs)
