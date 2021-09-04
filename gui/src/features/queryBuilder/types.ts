export interface Column {
  key: string;
  name: string;
}

export interface Grid {
  columns: Column[];
  rows: Record<string, any>[];
}

export interface Editor {
  value: string;
  error?: string;
  running: boolean;
}

export interface QueryBuilderState {
  editor: Editor;
  grid: Grid;
}
