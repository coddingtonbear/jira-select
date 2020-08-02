from typing import Any, List, Union, Dict, Tuple, Optional
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
WhereParamDict = Dict[str, Any]

Expression = str

ExpressionList = List[Expression]

# We have to use the alternative method of defining the TypedDict since
# one of our dictionary fields' names is a reserved word
QueryDefinition = TypedDict(
    "QueryDefinition",
    {
        "select": List[Field],
        "from": DataSource,
        "where": Union[JqlList, WhereParamDict],
        "order_by": JqlList,
        "filter": ExpressionList,
        "having": ExpressionList,
        "group_by": ExpressionList,
        "sort_by": ExpressionList,
        "expand": List[str],
        "limit": int,
        "cap": int,
        "cache": Union[int, Tuple[Optional[int], Optional[int]]],
    },
    total=False,
)


class SchemaRow(TypedDict, total=False):
    id: str
    type: str
    description: str
    raw: Any


class ViewerDefinitionDict(TypedDict, total=False):
    csv: str


class ShellConfigDict(TypedDict, total=False):
    emacs_mode: bool


class InstanceDefinition(TypedDict, total=False):
    url: str
    username: str
    password: str
    verify: Union[str, bool]


class ConfigDict(TypedDict, total=False):
    instances: Dict[str, InstanceDefinition]
    shell: ShellConfigDict
    viewers: ViewerDefinitionDict
