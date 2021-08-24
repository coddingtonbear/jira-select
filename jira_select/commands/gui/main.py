import wx

from .editor import EVT_RUN_QUERY
from .editor import EditorPanel
from .editor import RunQueryEvent
from .grid import GridPanel


class JiraSelectFrame(wx.Frame):
    def run_query(self, evt: RunQueryEvent):
        print(evt.data)

    def __init__(self):
        super().__init__(parent=None, title="Jira Select")

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(EditorPanel(self), proportion=1, flag=wx.EXPAND)
        main_sizer.Add(GridPanel(self), proportion=2, flag=wx.EXPAND)
        main_sizer.SetSizeHints(self)

        self.Bind(EVT_RUN_QUERY, self.run_query)

        self.SetSizerAndFit(main_sizer)
        self.Show()
