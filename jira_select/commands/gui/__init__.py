import wx

from jira_select.plugin import BaseCommand

from .main import JiraSelectFrame


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return "Opens an interactive query editor GUI."

    def handle(self) -> None:
        app = wx.App()

        frame = JiraSelectFrame()

        app.MainLoop()
