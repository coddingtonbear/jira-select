import wx
from wx import grid


class Grid(grid.Grid):
    _created = False
    _column_count = 0
    _row_count = 0

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.EnableEditing(False)

    def CreateGrid(self, numRows, numCols):
        if self._created:
            self.DeleteCols(pos=0, numCols=self._column_count)
            self.DeleteRows(pos=0, numRows=self._row_count)

            self.AppendCols(numCols=numCols)
            self.AppendRows(numRows=numRows)
            return

        self._column_count = numCols
        self._row_count = numRows
        self._created = True
        return super().CreateGrid(numRows, numCols, selmode=grid.Grid.GridSelectCells)


class GridPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_view = Grid(self)
        self.grid_view.ShowScrollbars(True, True)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid_view, proportion=1, flag=wx.EXPAND)
        sizer.SetSizeHints(self)

        self.SetSizer(sizer)
