from __future__ import annotations

import hashlib
import logging
import os
import re
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    Tuple,
    Mapping,
)

from appdirs import user_config_dir
from jira.resources import Resource
import simpleeval
from simpleeval import EvalWithCompoundTypes
from yaml import safe_dump, safe_load

from .constants import APP_NAME
from .exceptions import FieldNameError, QueryError, JiraSelectError
from .types import (
    ConfigDict,
    ExpressionList,
    SelectFieldDefinition,
    Expression,
)

if TYPE_CHECKING:
    from .query import Result

FIELD_DISPLAY_DEFN_RE = re.compile(r'^(?P<expression>.*) as "(?P<column>.*)"$')
SORT_BY_DESC_FN = re.compile(r"^(?P<expression>.*) DESC", re.IGNORECASE)
SORT_BY_ASC_FN = re.compile(r"^(?P<expression>.*) ASC", re.IGNORECASE)


logger = logging.getLogger(__name__)


def get_config_dir() -> str:
    root_path = user_config_dir(APP_NAME, "coddingtonbear")
    os.makedirs(root_path, exist_ok=True)

    return root_path


def get_cache_path(subcache: str = "default") -> str:
    config_path = get_config_dir()
    cache_path = os.path.join(config_path, "cache", subcache)
    os.makedirs(cache_path, exist_ok=True)

    return cache_path


def get_default_config_path() -> str:
    root_path = get_config_dir()
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


def parse_sort_by_definition(expression: str) -> Tuple[str, bool]:
    is_reversed = False
    is_reversed_match = SORT_BY_DESC_FN.match(expression)
    is_not_reversed_match = SORT_BY_ASC_FN.match(expression)
    if is_reversed_match:
        expression = is_reversed_match.groupdict()["expression"]
        is_reversed = True
    elif is_not_reversed_match:
        expression = is_not_reversed_match.groupdict()["expression"]
        is_reversed = False

    return expression, is_reversed


def calculate_result_hash(
    row: Result, group_fields: ExpressionList, functions: Dict[str, Callable],
) -> int:
    params = [
        str(get_field_data(row, group_field, functions)) for group_field in group_fields
    ]

    return int(hashlib.sha1(":".join(params).encode("UTF-8")).hexdigest(), 16)


def get_row_dict(row: Any) -> Dict[str, Any]:
    names: Dict[str, Any] = {}

    if hasattr(row, "fields"):
        for field_name in dir(row.fields):
            if not field_name.startswith("_"):
                names[field_name] = getattr(row.fields, field_name)

    # Gather any top-level keys, too, to make sure we fetch any expansions
    for key in dir(row):
        if key != "fields" and not key.startswith("_") and not key.upper() == key:
            names[key] = getattr(row, key)

    return names


def expression_includes_group_by(
    expression: Expression, group_by: List[Expression]
) -> bool:
    for group_by_expression in group_by:
        if group_by_expression in expression:
            return True

    return False


def evaluate_expression(
    expression: str,
    names: Dict[str, Any],
    functions: Optional[Dict[str, Callable]] = None,
    interpolations: Optional[Mapping[str, Any]] = None,
) -> Any:
    try:
        expression = expression.format_map(interpolations or {})
    except KeyError as e:
        raise FieldNameError(e)

    return EvalWithCompoundTypes(names=names, functions=functions).eval(expression)


def normalize_value(value: Any) -> Any:
    if isinstance(value, (str, bool, float, int)):
        return value
    elif isinstance(value, list):
        return [normalize_value(v) for v in value]
    elif isinstance(value, Dict):
        return {k: normalize_value(v) for k, v in value.items()}
    elif isinstance(value, Resource):
        display = str(value)
        if display.startswith("<JIRA"):
            # If the display value starts with "<JIRA", we know
            # the library couldn't find a pretty way of printing
            # this field; let's just return the raw dictionary
            # in that case
            return value.raw
        return display
    elif "PropertyHolder" in str(value):
        # Yes; this LOOKS ridiculous, but in older versions
        # of the Jira library, the PropertyHolder class is
        # created a runtime :facepalm:.  I think this is
        # the only way to find them :shrug:
        return {
            name: normalize_value(getattr(value, name))
            for name in dir(value)
            if not name.startswith("_") and not name.upper() == name
        }

    return value


def get_field_data(
    row: Result,
    expression: str,
    functions: Optional[Dict[str, Callable]] = None,
    interpolations: Optional[Mapping[str, Any]] = None,
    error_returns_null=True,
) -> Any:
    if functions is None:
        functions = {}

    try:
        return normalize_value(
            evaluate_expression(
                expression,
                names={"_": row, **row.as_dict()},
                functions=functions,
                interpolations=interpolations,
            )
        )
    except FieldNameError as e:
        raise QueryError(f"Field {e} does not exist.") from e
    except JiraSelectError:
        # Re-raise these -- they can be used for alerting the user
        # to a configuration problem or w/e
        raise
    except (
        simpleeval.AttributeDoesNotExist,
        simpleeval.NameNotDefined,
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
    ):
        if not error_returns_null:
            raise
        return None
    except Exception as e:
        raise QueryError(f"{e}: {expression}") from e
