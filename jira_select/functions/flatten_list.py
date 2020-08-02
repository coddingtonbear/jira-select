from typing import Any, List

from ..plugin import BaseFunction


class Function(BaseFunction):
    def __call__(self, scalar: List[List[Any]]) -> Any:  # type: ignore[override]
        return [item for sublist in scalar if sublist for item in sublist if item]
