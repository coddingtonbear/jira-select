from __future__ import annotations

import copy
import importlib.util
import json
import logging
import os
import random
import statistics
from abc import ABCMeta
from abc import abstractmethod
from typing import IO
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Type

import keyring
from jira import JIRA
from rich.console import Console
from rich.progress import TaskID
from safdie import BaseCommand as SafdieBaseCommand
from safdie import get_entrypoints
from urllib3 import disable_warnings

from .constants import APP_NAME
from .constants import FORMATTER_ENTRYPOINT
from .constants import FUNCTION_ENTRYPOINT
from .constants import SOURCE_ENTRYPOINT
from .exceptions import ConfigurationError
from .types import ConfigDict
from .types import InstanceDefinition
from .types import SchemaRow
from .types import SelectFieldDefinition
from .utils import get_custom_function_dir
from .utils import get_functions_for_module
from .utils import save_config

if TYPE_CHECKING:
    from .query import CounterChannel
    from .query import Executor
    from .query import Query

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
    **get_functions_for_module(
        random,
        ["random", "randrange", "randint", "choice"],
    ),
    # JSON
    "json_loads": json.loads,
}
REGISTERED_FUNCTIONS: Dict[str, Callable] = {}


class BaseCommand(SafdieBaseCommand):
    _jira: Optional[JIRA] = None

    def __init__(self, *, config: ConfigDict, **kwargs):
        self._config: ConfigDict = config
        self._console = Console(highlight=False)
        super().__init__(**kwargs)

    @property
    def config(self) -> ConfigDict:
        """Provides the configuration dictionary."""
        return self._config

    def save_config(self) -> None:
        """Saves the existing configuration dictionary."""
        save_config(self.config, self.options.config)

    @property
    def console(self) -> Console:
        """Provides access to the console (see `rich.console.Console`."""
        return self._console

    @property
    def jira(self) -> JIRA:
        """Provides access to the configured Jira instance."""
        if self._jira is None:
            instance = self.config.instances.get(
                self.options.instance_name, InstanceDefinition()
            )

            instance_url = self.options.instance_url or instance.url
            if not instance_url:
                raise ConfigurationError(
                    "instance_url not set; please run `jira-select configure`."
                )

            username = self.options.username or instance.username
            if not username:
                raise ConfigurationError(
                    "username not set; please run `jira-select configure`."
                )

            password = self.options.password or instance.password
            if not password:
                password = keyring.get_password(APP_NAME, instance_url + username)
                if not password:
                    raise ConfigurationError(
                        f"Password not stored for {instance_url} user {username}; "
                        "use the 'store-password' command to store the password "
                        "for this user account in your system keyring or use "
                        "`jira-select configure`."
                    )

            verify = self.options.disable_certificate_verification or instance.verify
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


def get_installed_formatters() -> Dict[str, Type[BaseFormatter]]:
    return get_entrypoints(FORMATTER_ENTRYPOINT, BaseFormatter)


class BaseFormatter(metaclass=ABCMeta):
    def __init__(self, executor: Executor, stream: IO[bytes]):
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


def register_function(fn: Callable):
    """Register a callable to be a function available in queries."""
    REGISTERED_FUNCTIONS[fn.__name__] = fn


def get_installed_functions(
    jira: JIRA = None, query: Query = None
) -> Dict[str, Callable]:
    possible_commands: Dict[str, Callable] = copy.copy(BUILTIN_FUNCTIONS)

    # Import any modules in the custom functions directory; as a
    # side-effect of this, the functions will become listed within
    # REGISTERED_FUNCTIONS
    function_dir = get_custom_function_dir()
    for dirname, subdirlist, filelist in os.walk(function_dir):
        for filename in filelist:
            if filename.endswith(".py"):
                module_path_parts = ["user_scripts"]
                if dirname != function_dir:
                    module_path_parts.append(
                        dirname[len(function_dir) + 1 :]
                        .replace("/", ".")
                        .replace("\\", ".")
                    )
                module_path_parts.append(os.path.splitext(filename)[0])
                module_path = ".".join(module_path_parts)

                full_path = os.path.join(function_dir, dirname, filename)
                try:
                    spec = importlib.util.spec_from_file_location(
                        module_path, full_path
                    )
                    if not spec:
                        continue
                    user_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(user_module)  # type: ignore
                except Exception as e:
                    logger.error("Could not import user script at %s: %s", full_path, e)

    possible_commands.update(REGISTERED_FUNCTIONS)

    for fn_name, fn in get_entrypoints(FUNCTION_ENTRYPOINT, BaseFunction).items():
        possible_commands[fn_name] = fn(jira, query=query)

    return possible_commands


class BaseFunction(metaclass=ABCMeta):
    def __init__(self, jira: Optional[JIRA], query: Optional[Query]):
        self._jira = jira
        self._query = query

    @property
    def query(self) -> Optional[Query]:
        return self._query

    @property
    def jira(self):
        assert self._jira

        return self._jira

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Optional[Any]:
        ...


def get_installed_sources() -> Dict[str, Type[BaseSource]]:
    return get_entrypoints(SOURCE_ENTRYPOINT, BaseSource)


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
                SelectFieldDefinition(
                    expression=entry.id,
                    column=entry.id,
                )
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
