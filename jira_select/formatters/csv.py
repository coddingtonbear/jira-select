import csv
from io import TextIOWrapper
from typing import Any
from typing import Dict
from typing import List

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    delimiter = ","

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
        self._wrapped_stream = TextIOWrapper(
            self.stream, encoding="utf-8", write_through=True, newline=""
        )
        self.out = csv.DictWriter(
            self._wrapped_stream,
            fieldnames=self._generate_fieldnames(),
            delimiter=self.delimiter,
        )
        self.out.writeheader()

    def close(self):
        self._wrapped_stream.detach()

    def writerow(self, row: Dict[str, Any]):
        self.out.writerow(row)
