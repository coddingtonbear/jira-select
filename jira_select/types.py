from typing import Any, Callable, Dict, List, Literal, Union
from typing_extensions import TypedDict


DataSource = Literal["issues", "boards"]


class SelectFieldDefinition(TypedDict):
    field: str
    display: str


Field = Union[SelectFieldDefinition, str]

JQLString = str

CustomFilterFieldName = str


class JQLIssueQuery(TypedDict):
    jql: JQLString


ListIssueQuery = List


# We have to use the alternative method of defining the TypedDict since
# one of our dictionary fields' names is a reserved word
QueryDefinition = TypedDict(
    "QueryDefinition",
    {
        "select": List[Field],
        "from": DataSource,
        "where": Dict,
        "expand": List[str],
        # "having": Dict[CustomFilterFieldName, Any],
    },
    total=False,
)


class ConfigDict(TypedDict, total=False):
    instance_url: str
    username: str
    password: str
    viewer: str  # App to use for viewing CSV


class Question(TypedDict, total=False):
    type: Literal[
        "confirm", "checkbox", "expand", "input", "list", "password", "rawlist"
    ]
    name: str
    message: str
    default: Any
    validate: Callable
    filter: Callable
    when: Callable
    choices: List[Any]
