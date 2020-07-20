from typing import Any, List

from ..plugin import BaseFunction


class Function(BaseFunction):
    def __call__(self, scalar: List[Any], dotpath: str) -> Any:  # type: ignore[override]
        values = []

        path_parts = dotpath.split(".")

        for item in scalar:
            if item is None:
                continue

            try:
                cursor = item
                for part in path_parts:
                    if isinstance(cursor, dict):
                        cursor = cursor[part]
                    else:
                        cursor = getattr(cursor, part)
            except (KeyError, AttributeError):
                continue

            if cursor is not None:
                values.append(cursor)

        return values
