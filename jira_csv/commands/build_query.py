from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Interactively generates a query definition (in yaml format)."

    def handle(self) -> None:
        raise NotImplementedError()

