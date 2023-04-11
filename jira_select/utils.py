from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Union

import simpleeval
from appdirs import user_config_dir
from jira.resources import Resource
from portion import Interval
from pytz import UTC
from simpleeval import EvalWithCompoundTypes
from yaml import safe_dump
from yaml import safe_load

from .constants import APP_NAME
from .exceptions import FieldNameError
from .exceptions import JiraSelectError
from .exceptions import QueryError
from .exceptions import UnhandledConditionError
from .types import ConfigDict
from .types import Expression
from .types import ExpressionList
from .types import SelectFieldDefinition

if TYPE_CHECKING:
    from .query import Result

FIELD_DISPLAY_DEFN_RE = re.compile(r'^(?P<expression>.*) as "(?P<column>.*)"$')
SORT_BY_DESC_FN = re.compile(r"^(?P<expression>.*) DESC", re.IGNORECASE)
SORT_BY_ASC_FN = re.compile(r"^(?P<expression>.*) ASC", re.IGNORECASE)
PARAM_FINDER = re.compile(r"{params\.([^}.]+)(?:.[^}.]+)?}")

ISO_FORMAT = "%Y-%m-%d %H:%M:%SZ"


logger = logging.getLogger(__name__)


class JiraSelectJsonEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        from .functions.flatten_changelog import ChangelogEntry

        if isinstance(obj, datetime.datetime):
            return UTC.normalize(obj).strftime(ISO_FORMAT)
        elif isinstance(obj, ChangelogEntry):
            return {
                "author": obj.author,
                "created": UTC.normalize(obj.created).strftime(ISO_FORMAT)
                if obj.created
                else None,
                "field": obj.field,
                "fieldtype": obj.fieldtype,
                "fromValue": obj.fromValue,
                "fromString": obj.fromString,
                "toValue": obj.toValue,
                "toString": obj.toString,
            }
        elif isinstance(obj, Interval):
            interval_list = []
            for interval in list(obj):
                interval_list.append(
                    (
                        interval.lower,
                        interval.upper,
                    )
                )
            return interval_list
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def get_config_dir() -> str:
    root_path = user_config_dir(APP_NAME, "coddingtonbear")
    os.makedirs(root_path, exist_ok=True)

    return root_path


def get_custom_function_dir() -> str:
    root_path = os.path.join(user_config_dir(APP_NAME, "coddingtonbear"), "functions")
    os.makedirs(root_path, exist_ok=True)

    return root_path


def get_cache_path(subcache: str = "default") -> str:
    config_path = get_config_dir()
    cache_path = os.path.join(config_path, "cache", subcache)
    os.makedirs(cache_path, exist_ok=True)

    return cache_path


def get_default_config_path() -> str:
    root_path = get_config_dir()
    return os.path.join(
        root_path,
        "config.yaml",
    )


def get_config(path: str = None) -> ConfigDict:
    if path is None:
        path = get_default_config_path()

    if not os.path.isfile(path):
        return ConfigDict()

    with open(path, "r") as inf:
        return ConfigDict.parse_obj(safe_load(inf))


def save_config(data: ConfigDict, path: str = None) -> None:
    if path is None:
        path = get_default_config_path()

    with open(path, "w") as outf:
        safe_dump(data.dict(), outf)


def get_functions_for_module(
    module: ModuleType, names: List[str]
) -> Dict[str, Callable]:
    """Return functions in module matching the specified name.

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

        return SelectFieldDefinition(expression=expression, column=column)
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
    row: Result,
    group_fields: ExpressionList,
    functions: Dict[str, Callable],
) -> int:
    params = [
        str(get_field_data(row, group_field, functions)) for group_field in group_fields
    ]

    return int(hashlib.sha1(":".join(params).encode("UTF-8")).hexdigest(), 16)


def get_row_dict(row: Any, overlay: dict[str, Any] | None = None) -> Dict[str, Any]:
    names: dict[str, Any] = {}

    if hasattr(row, "fields"):
        for field_name in dir(row.fields):
            if not field_name.startswith("_"):
                names[field_name] = getattr(row.fields, field_name)

    # Gather any top-level keys, too, to make sure we fetch any expansions
    for key in dir(row):
        if key != "fields" and not key.startswith("_") and not key.upper() == key:
            names[key] = getattr(row, key)

    names.update(overlay if overlay is not None else {})

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
                names={
                    "_": row,  # Pre 3.0 queries
                    "issue": row,  # Post-3.0 queries
                    **row.as_dict(),
                },
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
    ) as e:
        logger.warning(
            "%s while evaluating expression %s for issue(s) %s: %s",
            e.__class__.__name__,
            expression,
            row.key,
            e,
        )
        if not error_returns_null:
            raise
        return None
    except Exception as e:
        raise QueryError(f"{e}: {expression}") from e


def launch_default_viewer(relpath: str) -> None:
    path = os.path.abspath(relpath)

    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.call(["open", path])
    elif sys.platform == "linux":
        subprocess.call(["xdg-open", path])
    else:
        raise UnhandledConditionError(
            "Could not determine method of launching default "
            f"interpreter for platform {sys.platform}."
        )


def find_missing_parameters(expression: str, known_params: List[str]) -> List[str]:
    missing_parameters: List[str] = []

    expression_params = PARAM_FINDER.findall(expression)
    for expression_param in expression_params:
        if expression_param not in known_params:
            missing_parameters.append(expression_param)

    return missing_parameters
