from typing import Dict
from typing import Hashable
from typing import Iterator
from typing import Optional
from typing import Union

from jira.exceptions import JIRAError
from jira.resources import Sprint

from ..exceptions import UserError
from ..plugin import BaseFunction


class Function(BaseFunction):
    """Returns a `jira.resources.Sprint` object for a given sprint ID string."""

    CACHE: Dict[Hashable, Sprint] = {}

    def get_sprint_iterator(
        self, board_name_or_id: Union[str, int]
    ) -> Iterator[Sprint]:
        if isinstance(board_name_or_id, int):
            is_last = False
            start_at = 0

            while not is_last:
                try:
                    sprints = self.jira.sprints(
                        board_name_or_id, startAt=start_at, maxResults=50
                    )
                except JIRAError:
                    break

                is_last = sprints.isLast
                for sprint in sprints:
                    yield sprint
                    start_at += 1
        else:
            board_start = 0
            board_is_last = False

            while not board_is_last:
                boards = self.jira.boards(
                    startAt=board_start, maxResults=50, name=board_name_or_id
                )

                board_is_last = boards.isLast
                for board in boards:
                    is_last = False
                    start_at = 0

                    while not is_last:
                        try:
                            sprints = self.jira.sprints(
                                board.id, startAt=start_at, maxResults=50
                            )
                        except JIRAError:
                            break

                        is_last = sprints.isLast
                        for sprint in sprints:
                            yield sprint
                            start_at += 1

                    board_start += 1

    def get_sprint_details(
        self, board_name_or_id: Union[str, int], sprint_name: str
    ) -> Sprint:
        cache_key = (
            board_name_or_id,
            sprint_name,
        )

        if cache_key not in self.CACHE:
            sprints = list(
                filter(
                    lambda sprint: sprint_name.lower() in sprint.name.lower(),
                    self.get_sprint_iterator(board_name_or_id),
                )
            )

            if len(sprints) == 0:
                raise UserError(
                    f"No sprint found on board {board_name_or_id} "
                    f"named {sprint_name}."
                )
            elif len(sprints) > 1:
                raise UserError(
                    f"More than one sprint was found on {board_name_or_id} "
                    f"having a name like {sprint_name}: {sprints}."
                )

            self.CACHE[cache_key] = Sprint(
                {"agile_rest_path": self.jira._options["agile_rest_path"]},
                None,
                sprints[0].raw,
            )

        return self.CACHE[cache_key]

    def __call__(self, board_name_or_id: Union[str, int], sprint_name: str) -> Optional[Sprint]:  # type: ignore[override]
        if board_name_or_id is None or sprint_name is None:
            return None

        return self.get_sprint_details(board_name_or_id, sprint_name)
