from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from pydantic import BaseModel
from pydantic import Field as ModelField
from typing_extensions import TypedDict

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


class QueryDefinition(BaseModel):
    select: List[Field]
    from_: str = ModelField(alias="from")
    where: Union[JqlList, WhereParamDict] = ModelField(default_factory=list)
    order_by: JqlList = ModelField(default_factory=list)
    filter_: ExpressionList = ModelField(alias="filter", default_factory=list)
    having: ExpressionList = ModelField(default_factory=list)
    group_by: ExpressionList = ModelField(default_factory=list)
    sort_by: ExpressionList = ModelField(default_factory=list)
    expand: ExpressionList = ModelField(default_factory=list)
    limit: Optional[int]
    cap: Optional[int]
    cache: Optional[Union[int, Tuple[Optional[int], Optional[int]]]]


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
