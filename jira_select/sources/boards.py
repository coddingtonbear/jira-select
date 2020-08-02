from typing import Dict, Iterator, List

from jira.resources import Board

from ..exceptions import QueryError
from ..plugin import BaseSource
from ..types import SelectFieldDefinition


class Source(BaseSource):
    FIELDS: List[SelectFieldDefinition] = [
        {"expression": "id", "column": "id",},
        {"expression": "self", "column": "self",},
        {"expression": "name", "column": "name",},
        {"expression": "type", "column": "type",},
    ]

    def __iter__(self) -> Iterator[Dict]:
        start_at = 0
        max_results = 2 ** 32
        result_limit = self.query.limit or 2 ** 32

        if self.query.where:
            raise QueryError(
                "Board queries do not support 'where' expressions; "
                "use a 'filter' expression instead."
            )

        self.update_progress(completed=0, total=1, visible=True)
        while start_at < min(max_results, result_limit):
            results = self.jira.boards(
                startAt=start_at, maxResults=min(result_limit, 100),
            )

            max_results = results.total
            count = min([results.total, result_limit])
            self.update_count(count)

            for result in results:
                self.update_progress(advance=1, total=count, visible=True)

                yield result.raw

                start_at += 1

                # Return early if our result limit has been reached
                if start_at >= result_limit:
                    break

    def rehydrate(self, value: Dict) -> Board:
        return Board(
            {"agile_rest_path": self.jira._options["agile_rest_path"]}, None, value
        )
