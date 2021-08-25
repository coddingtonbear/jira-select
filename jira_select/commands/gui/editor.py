import textwrap

import wx
import wx.lib.newevent
import wx.stc as stc
from wx.core import Event

RunQueryEvent, EVT_RUN_QUERY = wx.lib.newevent.NewCommandEvent()

QueryUpdatedEvent, EVT_QUERY_UPDATED = wx.lib.newevent.NewCommandEvent()


class YamlStyledTextCtrl(stc.StyledTextCtrl):
    def OnQueryUpdated(self, evt: Event):
        evt = QueryUpdatedEvent(self.GetId(), data=self.GetText())
        wx.PostEvent(self, evt)

    def __init__(self, parent):
        super().__init__(parent)

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

    def __init__(self, parent):
        super().__init__(parent)

        self.yaml_view = YamlStyledTextCtrl(self)

        query_button = wx.Button(self, label="Run Query")
        query_button.Bind(wx.EVT_BUTTON, self.OnRunQuery)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.yaml_view, proportion=1, flag=wx.EXPAND)
        sizer.Add(query_button, proportion=0, flag=wx.EXPAND)

        self.SetSizer(sizer)
