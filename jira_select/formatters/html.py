from typing import Any
from typing import Dict
from typing import List

from ..plugin import BaseFormatter


class Formatter(BaseFormatter):
    _fields: List[str]

    @classmethod
    def get_file_extension(cls) -> str:
        return "html"

    def open(self):
        super().open()

        self._fields = []

        for field in self.executor.query.select:
            self._fields.append(field.column)

        self.stream.write(
            b"""
            <!DOCTYPE html>
            <html>
                <head>
                    <style type="text/css">
                        body {
                            font-family: sans-serif;
                        }
                        table {
                            border-collapse: collapse;
                        }
                        td {
                            padding: 5px 10px;
                        }
                        tr {
                            border-bottom: 1px dotted black;
                        }
                    </style>
                </head>
                <body>
                    <table>
                        <thead>
                            <tr>
        """
        )
        for fieldname in self._fields:
            self.stream.write(f"<th>{fieldname}</th>".encode("utf-8"))

        self.stream.write(
            b"""
                </tr>
            </thead>
            <tbody>
        """
        )

    def close(self):
        self.stream.write(
            b"""
                        </tbody>
                    </table>
                </body>
            </html>
        """
        )
        return super().close()

    def writerow(self, row: Dict[str, Any]):
        self.stream.write(b"<tr>")
        for field in self._fields:
            self.stream.write(f"<td>{row.get(field)}</td>".encode("utf-8"))
        self.stream.write(b"</tr>")
