from __future__ import annotations

import hashlib
import logging
import os
import re
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from appdirs import user_config_dir
import simpleeval
from yaml import safe_dump, safe_load

from .constants import APP_NAME
from .types import ConfigDict, ExpressionList, QueryDefinition, SelectFieldDefinition

if TYPE_CHECKING:
    from .query import Result

FIELD_DISPLAY_DEFN_RE = re.compile(r'^(?P<expression>.*) as "(?P<column>.*)"$')
ORDER_BY_DESC_FN = re.compile(r"^(?P<expression>.*) DESC", re.IGNORECASE)


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


def get_functions_for_module(
    module: ModuleType, names: List[str]
) -> Dict[str, Callable]:
    """ Return functions in module matching the specified name.

    This exists because some functions we want to publish as available
    functions are available only on Python >= 3.8.

    """
    functions: Dict[str, Callable] = {}

    for name in names:
        if hasattr(module, name):
            functions[name] = getattr(module, name)

    return functions


def clean_query_definition(query: QueryDefinition) -> QueryDefinition:
    cleaned_query: QueryDefinition = {
        "select": [],
        "from": query["from"],
    }

    for select in query["select"]:
        if isinstance(select, dict):
            cleaned_query["select"].append(select)
        else:
            cleaned_query["select"].append(str(select))

    for section in (
        "where",
        "having",
        "group_by",
        "order_by",
        "expand",
    ):
        if section in query:
            # I'm not sure I understand why the typing checks here are failing
            cleaned_query[section] = [str(line) for line in query[section]]  # type: ignore

    if "limit" in query:
        cleaned_query["limit"] = query["limit"]

    return cleaned_query


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


def parse_order_by_definition(expression: str):
    is_reversed = ORDER_BY_DESC_FN.match(expression)

    if is_reversed:
        expression = is_reversed.groupdict()["expression"]

        return f"-1 * ({expression})"

    return expression


def calculate_result_hash(
    row: Result, group_fields: ExpressionList, functions: Dict[str, Callable],
) -> int:
    params = [
        str(get_field_data(row, group_field, functions)) for group_field in group_fields
    ]

    return int(hashlib.sha1(":".join(params).encode("UTF-8")).hexdigest(), 16)


def field_name_is_public(key: str) -> bool:
    if key.lower() == key and key != "fields" and not key.startswith("_"):
        return True

    return False


def get_row_dict(row: Any) -> Dict[str, Any]:
    names: Dict[str, Any] = {}

    if hasattr(row, "fields"):
        for field_name in dir(row.fields):
            if field_name_is_public(field_name):
                names[field_name] = getattr(row.fields, field_name)

    # Gather any top-level keys, too, to make sure we fetch any expansions
    for key in dir(row):
        value = getattr(row, key)
        if field_name_is_public(key) and isinstance(
            value, (str, bool, float, int, list, dict)
        ):
            names[key] = getattr(row, key)

    return names


def expressions_match(left: str, right: str) -> bool:
    """ Verifies that the expressions passed-in match one another.

    This is used for determining when to force returning a single value
    when selecting columns from a grouped query.

    Right now, this just compares the string equality of the expressions;
    it might be better later to compare them using the ast parser.
    """
    return left.strip() == right.strip()


def evaluate_expression(
    expression: str,
    names: Dict[str, Any],
    functions: Optional[Dict[str, Callable]] = None,
) -> Any:
    return simpleeval.simple_eval(expression, names=names, functions=functions)


def get_field_data(
    row: Result,
    expression: str,
    functions: Optional[Dict[str, Callable]] = None,
    error_returns_null=True,
) -> Any:
    if functions is None:
        functions = {}

    try:
        return simpleeval.simple_eval(
            expression, names={"_": row, **row.as_dict()}, functions=functions
        )
    except (simpleeval.AttributeDoesNotExist, KeyError, IndexError, TypeError):
        if not error_returns_null:
            raise
        return None
