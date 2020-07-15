import logging
import os

from appdirs import user_config_dir
from yaml import safe_load, safe_dump

from .constants import APP_NAME
from .types import ConfigDict


logger = logging.getLogger(__name__)


def get_default_config_path() -> str:
    root_path = user_config_dir(APP_NAME, "coddingtonbear")
    os.makedirs(root_path, exist_ok=True)
    return os.path.join(root_path, "config.yaml",)


def get_config(path: str = None) -> ConfigDict:
    if path is None:
        path = get_default_config_path()

    if not os.path.isfile(path):
        return {}

    with open(path, "r") as inf:
        return safe_load(inf)


def save_config(data: ConfigDict, path: str = None) -> None:
    if path is None:
        path = get_default_config_path()

    with open(path, "w") as outf:
        safe_dump(data, outf)
