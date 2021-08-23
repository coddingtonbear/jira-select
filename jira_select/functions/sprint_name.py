from typing import Optional

from .sprint_details import Function as SprintDetailsFunction


class Function(SprintDetailsFunction):
    """Returns the name of the sprint matching the provided ID."""

    def __call__(self, sprint_id: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if sprint_id is None:
            return None

        info = self.get_sprint_details(sprint_id)
        if info is None:
            return None

        return info.name
