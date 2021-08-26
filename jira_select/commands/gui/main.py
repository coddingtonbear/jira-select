import threading
import traceback

import wx
from jira.client import JIRA
from yaml import safe_load

from jira_select.query import Executor
from jira_select.types import QueryDefinition

from .editor import EVT_RUN_QUERY
from .editor import EditorPanel
from .editor import RunQueryEvent
from .grid import GridPanel


class JiraSelectFrame(wx.Frame):
    _jira: JIRA

    @property
    def jira(self) -> JIRA:
        return self._jira

    def OnRunQuery(self, evt: RunQueryEvent):
        try:
            self.editor.OnRunningQuery()

            query_definition = QueryDefinition.parse_obj(safe_load(evt.data))
            thread = threading.Thread(target=self.RunQuery, args=(query_definition,))
            thread.start()
        except Exception:
            self.query_error_display.SetLabelText(traceback.format_exc())
            self.query_error_display.Show()
            self.grid.Hide()
            self.Layout()
            return

    def RunQuery(self, defn: QueryDefinition):
        query = Executor(self.jira, defn)
        self.SetGridValues(query)

    def SetGridValues(self, query: Executor):
        query_rows = list(query)

        self.grid.Show()
        self.query_error_display.Hide()
        self.Layout()

        self.grid.grid_view.CreateGrid(len(query_rows), len(query.query.select))

        for idx, field in enumerate(query.query.select):
            self.grid.grid_view.SetColLabelValue(idx, field.column)

        for row_idx, row in enumerate(query_rows):
            for col_idx, field in enumerate(query.query.select):
                self.grid.grid_view.SetCellValue(
                    row_idx, col_idx, str(row[field.column])
                )

        self.editor.OnFinishedRunningQuery()

    def __init__(self, jira: JIRA):
        super().__init__(parent=None, title="Jira Select")
        self._jira = jira

        # Start grid in a hidden state because we haven't yet
        # executed a query to populate it with
        self.grid = GridPanel(self)
        self.grid.Hide()

        self.editor = EditorPanel(self)

        self.query_error_display = wx.StaticText(self, label="")
        self.query_error_display.Hide()

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.editor, proportion=1, flag=wx.EXPAND)
        main_sizer.Add(self.query_error_display, proportion=2, flag=wx.EXPAND)
        main_sizer.Add(self.grid, proportion=2, flag=wx.EXPAND)

        self.Bind(EVT_RUN_QUERY, self.OnRunQuery)

        self.SetSizer(main_sizer)
        self.SetSize(size=(1000, 500))

        self.Show()
