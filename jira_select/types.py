from typing import Any, List, Union

from typing_extensions import TypedDict, Literal

DataSource = Literal["issues", "boards"]

JiraFieldName = str


class SelectFieldDefinition(TypedDict):
    expression: str
    column: str


Field = Union[SelectFieldDefinition, JiraFieldName]

JQLString = str

CustomFilterFieldName = str

JqlList = List[str]

ExpressionList = List[str]

# We have to use the alternative method of defining the TypedDict since
# one of our dictionary fields' names is a reserved word
QueryDefinition = TypedDict(
    "QueryDefinition",
    {
        "select": List[Field],
        "from": DataSource,
        "where": JqlList,
        "order_by": JqlList,
        "having": ExpressionList,
        "group_by": ExpressionList,
        "sort_by": ExpressionList,
        "expand": List[str],
        "limit": int,
    },
    total=False,
)


class SchemaRow(TypedDict, total=False):
    key: str
    type: str
    description: str
    raw: Any


class ViewerDefinitionDict(TypedDict, total=False):
    csv: str


class ConfigDict(TypedDict, total=False):
    instance_url: str
    username: str
    password: str
    viewers: ViewerDefinitionDict
