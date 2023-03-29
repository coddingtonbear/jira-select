from .csv import Formatter as CsvFormatter


class Formatter(CsvFormatter):
    delimiter = "\t"

    @classmethod
    def get_file_extension(cls) -> str:
        return "tsv"
