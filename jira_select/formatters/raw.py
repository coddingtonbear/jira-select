from typing import Any
from typing import Dict

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    @classmethod
    def get_file_extension(cls) -> str:
        return "raw"

    def writerow(self, row: Dict[str, Any]):
        for value in row.values():
            self.stream.write(str(value).encode("utf-8"))
            self.stream.write("\n".encode("utf-8"))
