import textwrap

import wx
import wx.lib.newevent
import wx.stc as stc
from wx.core import Event
from wx.core import KeyEvent

RunQueryEvent, EVT_RUN_QUERY = wx.lib.newevent.NewCommandEvent()

QueryUpdatedEvent, EVT_QUERY_UPDATED = wx.lib.newevent.NewCommandEvent()


class YamlStyledTextCtrl(stc.StyledTextCtrl):
    def OnQueryUpdated(self, evt: Event):
        evt = QueryUpdatedEvent(self.GetId(), data=self.GetText())
        wx.PostEvent(self, evt)

    def OnKeyDown(self, event: KeyEvent):
        keycode: int = event.GetKeyCode()
        ctrldown: bool = event.ControlDown()

        if keycode == wx.WXK_RETURN and ctrldown:
            self.GetParent().OnRunQuery(event)
            return

        event.Skip()

    def __init__(self, parent):
        super().__init__(parent, style=wx.TE_PROCESS_ENTER)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.SetLexer(stc.STC_LEX_YAML)

        self.Bind(stc.EVT_STC_CHANGE, self.OnQueryUpdated)

        self.SetText(
            textwrap.dedent(
                """
            select:
            - '*'
            from: issues
        """
            ).strip()
        )


class EditorPanel(wx.Panel):
    def OnRunQuery(self, evt: Event):
        evt = RunQueryEvent(self.GetId(), data=self.yaml_view.GetText())

        wx.PostEvent(self, evt)

    def OnRunningQuery(self):
        self.query_button.Disable()
        self.Refresh()

    def OnFinishedRunningQuery(self):
        self.query_button.Enable()
        self.Refresh()

    def __init__(self, parent):
        super().__init__(parent)

        self.yaml_view = YamlStyledTextCtrl(self)

        self.query_button = wx.Button(self, label="Run Query")
        self.query_button.Bind(wx.EVT_BUTTON, self.OnRunQuery)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.yaml_view, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.query_button, proportion=0, flag=wx.EXPAND)

        self.SetSizer(sizer)
