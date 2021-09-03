export interface Column {
  key: string;
  name: string;
}

export interface Grid {
  columns: Column[];
  rows: Record<string, any>[];
}

export interface QueryBuilderState {
  editor: {
    value: string;
  };
  grid: Grid;
}
