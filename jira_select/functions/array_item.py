from typing import Any, List, Optional

from ..plugin import BaseFunction


class Function(BaseFunction):
    def process(self, array: Optional[List[Any]], index: int) -> Optional[Any]:  # type: ignore[override]
        if array is None:
            return None

        try:
            return array[index]
        except IndexError:
            return None
