from typing import Any, Optional

from ..plugin import BaseFunction


class Function(BaseFunction):
    def process(self, *options) -> Optional[Any]:  # type: ignore[override]
        for option in options:
            if option is not None:
                return option

        return None
