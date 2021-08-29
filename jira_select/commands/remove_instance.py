from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return (
            "Removes configuration for a particular Jira instance. "
            "Specify the instance to remove via `--instance-name`."
        )

    def handle(self, *args, **kwargs) -> None:
        del self.config.instances[self.options.instance_name]
        self.save_config()
