import {
  JiraSelectFunction,
  JiraSelectSchemaItem,
} from "../../jira_select_client";

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
  insertString?: string;
}

export interface Sidebar {
  selected?: SidebarOption;
  shown: boolean;

  functions?: JiraSelectFunction[];
  schema: {
    issue?: JiraSelectSchemaItem[];
  };
}

export interface QueryBuilderState {
  editor: Editor;
  grid: Grid;
  sidebar: Sidebar;
}
