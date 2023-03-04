from typing import Dict
from typing import Iterator
from typing import List

from jira.exceptions import JIRAError
from jira.resources import Sprint

from ..exceptions import QueryError
from ..plugin import BaseSource
from ..types import SchemaRow


class Source(BaseSource):
    SCHEMA: List[SchemaRow] = [
        SchemaRow.parse_obj({"id": "id", "type": "int"}),
        SchemaRow.parse_obj({"id": "state", "type": "str"}),
        SchemaRow.parse_obj({"id": "name", "type": "str"}),
        SchemaRow.parse_obj({"id": "startDate", "type": "datestr"}),
        SchemaRow.parse_obj({"id": "endDate", "type": "datestr"}),
        SchemaRow.parse_obj({"id": "completeDate", "type": "datestr"}),
        SchemaRow.parse_obj({"id": "originBoardId", "type": "int"}),
    ]

    def __iter__(self) -> Iterator[Dict]:
        start_at = 0
        max_results = 2**32
        result_limit = self.query.limit or 2**32

        if self.query.order_by:
            raise QueryError(
                "Sprint query 'order_by' expressions are not supported. "
                "Use 'sort_by' instead."
            )
        if self.query.expand:
            raise QueryError("Sprint query 'expand' expressions are not supported. ")

        where = self.query.where or {}
        if where and not isinstance(where, dict):
            raise QueryError(
                "Sprint query 'where' expressions should be a dictionary "
                "having any of the following keys: 'board_type', "
                "'board_name', or 'state'."
            )

        param_board_type = where.pop("board_type", None)
        param_board_name = where.pop("board_name", None)
        param_state = where.pop("state", None)

        if where:
            raise QueryError(f"Unexpected 'where' parameters: {where}.")

        count = 0

        already_returned = set()

        self.update_progress(completed=0, total=1, visible=True)
        while start_at < min(max_results, result_limit):
            results = self.jira.boards(
                startAt=start_at,
                maxResults=min(result_limit, 100),
                type=param_board_type,
                name=param_board_name,
            )

            max_results = results.total

            for result in results:
                self.update_progress(advance=1, total=results.total, visible=True)

                sprint_start_at = 0
                is_last = False
                while not is_last:
                    try:
                        sprints = self.jira.sprints(
                            result.id,
                            startAt=sprint_start_at,
                            maxResults=50,
                            state=param_state,
                        )
                    except JIRAError:
                        break

                    is_last = sprints.isLast
                    for sprint in sprints:
                        sprint_start_at += 1

                        if sprint.id in already_returned:
                            continue

                        count += 1
                        self.update_count(count)

                        yield sprint.raw

                        already_returned.add(sprint.id)

                        # Return early if our result limit has been reached
                        if count >= result_limit:
                            break

                start_at += 1

    def rehydrate(self, value: Dict) -> Sprint:
        return Sprint(
            {"agile_rest_path": self.jira._options["agile_rest_path"]}, None, value
        )
