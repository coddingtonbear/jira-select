import wx
import wx.lib.newevent
import wx.stc as stc

RunQueryEvent, EVT_RUN_QUERY = wx.lib.newevent.NewEvent()


class YamlStyledTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)

        self.SetLexer(stc.STC_LEX_YAML)

        import textwrap

        self.SetText(
            textwrap.dedent(
                """
            from: issues
            select:
            - one
            - two
        """
            )
        )


class EditorPanel(wx.Panel):
    def on_run_query(self, evt: wx.Event):
        print("On Run Query")
        evt = RunQueryEvent(data=self.yaml_view.GetText())

        wx.PostEvent(self.GetParent(), evt)

    def __init__(self, parent):
        super().__init__(parent)

        self.yaml_view = YamlStyledTextCtrl(self)

        query_button = wx.Button(self, label="Run Query")
        query_button.Bind(wx.EVT_BUTTON, self.on_run_query)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.yaml_view, proportion=1, flag=wx.EXPAND)
        sizer.Add(query_button, proportion=0, flag=wx.EXPAND)

        self.SetSizer(sizer)
