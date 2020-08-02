from __future__ import annotations

from abc import ABCMeta, abstractmethod
import argparse
import copy
import json
import logging
import random
import statistics
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    cast,
    Iterator,
    List,
)

import pkg_resources

import keyring
from jira import JIRA
from rich.console import Console
from rich.progress import TaskID
from urllib3 import disable_warnings

from .constants import APP_NAME
from .exceptions import ConfigurationError
from .types import ConfigDict, InstanceDefinition, SelectFieldDefinition, SchemaRow
from .utils import save_config, get_functions_for_module

if TYPE_CHECKING:
    from .query import Executor, CounterChannel, Query

logger = logging.getLogger(__name__)


BUILTIN_FUNCTIONS: Dict[str, Callable] = {
    # Built-ins
    "abs": abs,
    "all": all,
    "any": any,
    "bin": bin,
    "bool": bool,
    "hex": hex,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "map": map,
    "filter": filter,
    "type": lambda x: str(type(x)),
    # Statistics
    **get_functions_for_module(
        statistics,
        [
            "fmean",
            "geometric_mean",
            "harmonic_mean",
            "mean",
            "median",
            "median_grouped",
            "median_high",
            "median_low",
            "mode",
            "multimode",
            "pstdev",
            "pvariance",
            "quantiles",
            "stdev",
            "variance",
        ],
    ),
    # Random
    **get_functions_for_module(random, ["random", "randrange", "randint", "choice"],),
    # JSON
    "json_loads": json.loads,
    "json_dumps": json.dumps,
}
REGISTERED_FUNCTIONS: Dict[str, Callable] = {}


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
        self._console = Console(highlight=False)
        super().__init__()

    @property
    def config(self) -> ConfigDict:
        """ Provides the configuration dictionary."""
        return self._config

    def save_config(self) -> None:
        """ Saves the existing configuration dictionary."""
        save_config(self.config, self.options.config)

    @property
    def options(self) -> argparse.Namespace:
        """ Provides options provided at the command-line."""
        return self._options

    @property
    def console(self) -> Console:
        """ Provides access to the console (see `rich.console.Console`."""
        return self._console

    @property
    def jira(self) -> JIRA:
        """ Provides access to the configured Jira instance."""
        if self._jira is None:
            instance: Dict[InstanceDefinition] = cast(  # type: ignore
                InstanceDefinition,
                self.config.get("instances", {}).get(self.options.instance_name, {}),
            )

            instance_url = self.options.instance_url or instance.get("url")
            if not instance_url:
                raise ConfigurationError(
                    "instance_url not set; please run `jira-select configure`."
                )

            username = self.options.username or instance.get("username")
            if not username:
                raise ConfigurationError(
                    "username not set; please run `jira-select configure`."
                )

            password = self.options.password or instance.get("password")
            if not password:
                password = keyring.get_password(APP_NAME, instance_url + username)
                if not password:
                    raise ConfigurationError(
                        f"Password not stored for {instance_url} user {username}; "
                        "use the 'store-password' command to store the password "
                        "for this user account in your system keyring or use "
                        "`jira-select configure`."
                    )

            verify = self.options.disable_certificate_verification or instance.get(
                "verify"
            )
            if verify is None:
                verify = True
            if verify is False:
                disable_warnings()

            self._jira = JIRA(
                options={
                    "agile_rest_path": "agile",
                    "server": instance_url,
                    "verify": verify,
                },
                basic_auth=(username, password),
            )

        return self._jira

    @classmethod
    def get_help(cls) -> str:
        """ Retuurns help text for this function."""
        return ""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """ Allows adding additional command-line arguments. """
        pass

    @abstractmethod
    def handle(self) -> None:
        """ This is where the work of your function starts. """
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
    def __init__(self, executor: Executor, stream: IO[str]):
        self._executor = executor
        self._stream = stream

    @classmethod
    @abstractmethod
    def get_file_extension(cls) -> str:
        ...

    @property
    def executor(self):
        return self._executor

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


def register_function(name: str, fn: Callable):
    """ Register a callable to be a function available in queries."""
    REGISTERED_FUNCTIONS[name] = fn


def get_installed_functions(jira: JIRA = None) -> Dict[str, Callable]:
    possible_commands: Dict[str, Callable] = copy.copy(BUILTIN_FUNCTIONS)
    possible_commands.update(REGISTERED_FUNCTIONS)

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
        possible_commands[entry_point.name] = cast(Callable, loaded_class(jira))

    return possible_commands


class BaseFunction(metaclass=ABCMeta):
    def __init__(self, jira: Optional[JIRA]):
        self._jira = jira

    @property
    def jira(self):
        assert self._jira

        return self._jira

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Optional[Any]:
        ...


def get_installed_sources() -> Dict[str, Type[BaseSource]]:
    possible_sources: Dict[str, Type[BaseSource]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="jira_select.sources"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseSource):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jira_select.plugin.BaseSource`.",
                entry_point,
            )
            continue
        possible_sources[entry_point.name] = loaded_class

    return possible_sources


class BaseSource(metaclass=ABCMeta):
    SCHEMA: List[SchemaRow] = []

    def __init__(self, executor: Executor, task: TaskID, out_channel: CounterChannel):
        self._executor = executor
        self._task = task
        self._out_channel = out_channel

        super().__init__()

    @classmethod
    def get_schema(cls, jira: JIRA) -> List[SchemaRow]:
        return copy.deepcopy(cls.SCHEMA)

    @classmethod
    def get_all_fields(cls, jira: JIRA) -> List[SelectFieldDefinition]:
        fields: List[SelectFieldDefinition] = []

        for entry in cls.get_schema(jira):
            fields.append(
                {"expression": entry["id"], "column": entry["id"],}
            )

        return fields

    def remove_progress(self):
        self._executor.progress.remove_task(self._task)

    def update_progress(self, *args, **kwargs):
        self._executor.progress.update(self._task, *args, **kwargs)

    def update_count(self, value: int):
        self._out_channel.set(value)

    @property
    def query(self) -> Query:
        return self._executor.query

    @property
    def jira(self) -> JIRA:
        return self._executor.jira

    @abstractmethod
    def rehydrate(self, value: Any) -> Any:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        ...
