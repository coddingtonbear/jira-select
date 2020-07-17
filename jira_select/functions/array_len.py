from typing import Any, List, Optional

from ..plugin import BaseFunction


class Function(BaseFunction):
    def process(self, array: Optional[List[Any]]) -> Optional[int]:  # type: ignore[override]
        if array is None:
            return None

        try:
            return len(array)
        except IndexError:
            return None
