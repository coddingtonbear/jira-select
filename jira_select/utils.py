import logging
import os
import re
from typing import Any, Callable, Dict, Optional, Union

from appdirs import user_config_dir
from simpleeval import AttributeDoesNotExist, simple_eval
from yaml import safe_dump, safe_load

from .constants import APP_NAME
from .types import ConfigDict, SelectFieldDefinition

FIELD_DISPLAY_DEFN_RE = re.compile(r'^(?P<expression>.*) as "(?P<column>.*)"$')


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


def parse_select_definition(
    expression: Union[str, SelectFieldDefinition]
) -> SelectFieldDefinition:
    if isinstance(expression, str):
        as_match = FIELD_DISPLAY_DEFN_RE.match(expression)
        column = expression
        expression = expression
        if as_match:
            match_dict = as_match.groupdict()
            expression = match_dict["expression"]
            column = match_dict["column"]

        return {"expression": expression, "column": column}
    return expression


def get_field_data(
    row: Any, expression: str, functions: Optional[Dict[str, Callable]] = None
) -> Any:
    if functions is None:
        functions = {}

    names: Dict[str, Any] = {}
    if hasattr(row, "key"):
        names["key"] = row.key

    if hasattr(row, "fields"):
        for field_name in dir(row.fields):
            names[field_name] = getattr(row.fields, field_name)

    try:
        return simple_eval(expression, names=names, functions=functions)
    except AttributeDoesNotExist:
        return None
