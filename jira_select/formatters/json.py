import json
from io import TextIOWrapper
from typing import Any
from typing import Dict
from typing import List

from ..plugin import BaseFormatter
from ..utils import JiraSelectJsonEncoder


class Formatter(BaseFormatter):
    _rows: List[Dict] = []

    @classmethod
    def get_file_extension(cls) -> str:
        return "json"

    def open(self):
        super().open()
        self._rows = []

    def close(self):
        wrapped = TextIOWrapper(self.stream, encoding="utf-8", write_through=True)
        json.dump(self._rows, wrapped, cls=JiraSelectJsonEncoder, indent=4)
        wrapped.detach()
        super().close()

    def writerow(self, row: Dict[str, Any]):
        self._rows.append(row)
