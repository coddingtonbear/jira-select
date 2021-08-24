import wx
from wx import grid


class Grid(grid.Grid):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.CreateGrid(12, 8)


class GridPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_view = Grid(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid_view, proportion=1, flag=wx.EXPAND)
        sizer.SetSizeHints(self)

        self.SetSizer(sizer)
