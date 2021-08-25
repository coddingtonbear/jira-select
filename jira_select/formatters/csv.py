import csv
from typing import Any
from typing import Dict
from typing import List

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    @classmethod
    def get_file_extension(cls) -> str:
        return "csv"

    def _generate_fieldnames(self) -> List[str]:
        fields = []

        for field in self.executor.query.select:
            fields.append(field.column)

        return fields

    def open(self):
        super().open()
        self.out = csv.DictWriter(self.stream, fieldnames=self._generate_fieldnames())
        self.out.writeheader()

    def writerow(self, row: Dict[str, Any]):
        self.out.writerow(row)
