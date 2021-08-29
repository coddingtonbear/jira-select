from io import TextIOWrapper
from typing import Any
from typing import Dict
from typing import List

from rich.console import Console
from rich.table import Table

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    @classmethod
    def get_file_extension(cls) -> str:
        return "txt"

    def _generate_fieldnames(self) -> List[str]:
        fields = []

        for field in self.executor.query.select:
            fields.append(field.column)

        return fields

    def open(self):
        super().open()
        self.table = Table()

        for field in self.executor.query.select:
            self.table.add_column(field.column)

    def close(self):
        wrapped = TextIOWrapper(self.stream, encoding="utf-8", write_through=True)
        console = Console(file=wrapped)
        console.print(self.table)
        wrapped.detach()
        super().close()

    def writerow(self, row: Dict[str, Any]):
        fields = [str(row.get(field.column)) for field in self.executor.query.select]
        self.table.add_row(*fields)
