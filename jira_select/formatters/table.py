from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    @classmethod
    def get_file_extension(cls) -> str:
        return "csv"

    def _generate_fieldnames(self) -> List[str]:
        fields = []

        for field in self.executor.query.select:
            fields.append(field["column"])

        return fields

    def open(self):
        super().open()
        self.table = Table()

        for field in self.executor.query.select:
            self.table.add_column(field["column"])

    def close(self):
        console = Console()
        console.print(self.table)
        super().close()

    def writerow(self, row: Dict[str, Any]):
        fields = [str(row.get(field["column"])) for field in self.executor.query.select]
        self.table.add_row(*fields)
