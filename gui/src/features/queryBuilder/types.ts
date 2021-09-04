export type SidebarOption = "fieldnames" | "functions" | "code";

export interface Column {
  key: string;
  name: string;
}

export interface Grid {
  columns: Column[];
  rows: Record<string, any>[];
}

export interface Editor {
  error?: string;
  running: boolean;
}

export interface Sidebar {
  selected?: SidebarOption;
  shown: boolean;
}

export interface QueryBuilderState {
  editor: Editor;
  grid: Grid;
  sidebar: Sidebar;
}
