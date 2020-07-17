from typing import List, Literal, Union

from typing_extensions import TypedDict

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
        "having": ExpressionList,
        "expand": List[JiraFieldName],
        # "having": Dict[CustomFilterFieldName, Any],
    },
    total=False,
)


class ViewerDefinitionDict(TypedDict, total=False):
    csv: str


class ConfigDict(TypedDict, total=False):
    instance_url: str
    username: str
    password: str
    viewers: ViewerDefinitionDict
