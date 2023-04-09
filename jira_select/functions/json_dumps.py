import json
from typing import Optional

from ..plugin import BaseFunction
from ..utils import JiraSelectJsonEncoder


class Function(BaseFunction):
    """Dump an object as a JSON string."""

    def __call__(self, value: str, *args, **kwargs) -> Optional[str]:  # type: ignore[override]
        return json.dumps(value, cls=JiraSelectJsonEncoder, *args, **kwargs)
