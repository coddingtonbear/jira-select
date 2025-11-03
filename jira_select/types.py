from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict as PydanticConfigDict
from pydantic import Field as ModelField

JiraFieldName = str


class SelectFieldDefinition(BaseModel):
    expression: str
    column: str


Field = Union[SelectFieldDefinition, JiraFieldName]

JQLString = str

CustomFilterFieldName = str

JqlList = List[str]
WhereParamDict = Dict[str, Any]

Expression = str | bool | int

ExpressionList = Sequence[Expression]


class QueryDefinition(BaseModel):
    select: Union[List[Field], Dict[str, Optional[str]]]
    static: Dict[str, str] = ModelField(default_factory=dict, alias="static")
    calculate: Dict[str, str] = ModelField(default_factory=dict)
    from_: str = ModelField(alias="from")
    subqueries: Dict[str, "QueryDefinition"] = ModelField(default_factory=dict)
    where: Union[JqlList, WhereParamDict] = ModelField(default_factory=list)
    order_by: JqlList = ModelField(default_factory=list)
    filter_: ExpressionList = ModelField(alias="filter", default_factory=list)
    having: ExpressionList = ModelField(default_factory=list)
    group_by: ExpressionList = ModelField(default_factory=list)
    sort_by: ExpressionList = ModelField(default_factory=list)
    expand: ExpressionList = ModelField(default_factory=list)
    limit: Optional[int] = None
    cap: Optional[int] = None
    cache: Optional[Union[int, Tuple[Optional[int], Optional[int]]]] = None
    model_config = PydanticConfigDict(populate_by_name=True, extra="forbid")


QueryDefinition.model_rebuild()


class SchemaRow(BaseModel):
    id: str
    type: str
    description: Optional[str] = None
    raw: Optional[Any] = None


class ShellConfig(BaseModel):
    emacs_mode: Optional[bool] = False


class InstanceDefinition(BaseModel):
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify: Optional[Union[str, bool]] = True


class ConfigDict(BaseModel):
    instances: Dict[str, InstanceDefinition] = ModelField(default_factory=dict)
    shell: ShellConfig = ModelField(default_factory=ShellConfig)
    inline_viewers: Dict[str, str] = ModelField(default_factory=dict)
