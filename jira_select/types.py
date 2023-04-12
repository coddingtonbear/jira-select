from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from pydantic import BaseModel
from pydantic import Extra
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

Expression = str

ExpressionList = List[Expression]


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
    limit: Optional[int]
    cap: Optional[int]
    cache: Optional[Union[int, Tuple[Optional[int], Optional[int]]]]

    class Config:
        allow_population_by_field_name = True
        extra = Extra.forbid


QueryDefinition.update_forward_refs()


class SchemaRow(BaseModel):
    id: str
    type: str
    description: Optional[str]
    raw: Optional[Any]


class ShellConfig(BaseModel):
    emacs_mode: Optional[bool] = False


class InstanceDefinition(BaseModel):
    url: Optional[str]
    username: Optional[str]
    password: Optional[str]
    verify: Optional[Union[str, bool]] = True


class ConfigDict(BaseModel):
    instances: Dict[str, InstanceDefinition] = ModelField(default_factory=dict)
    shell: ShellConfig = ModelField(default_factory=ShellConfig)
    inline_viewers: Dict[str, str] = ModelField(default_factory=dict)
