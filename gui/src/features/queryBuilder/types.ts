import {
  JiraSelectFunction,
  JiraSelectInstance,
  JiraSelectSchemaItem,
} from "../../jira_select_client";

export type SidebarOption = "fieldnames" | "functions" | "code" | "settings";

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

export interface Schemas {
  issue?: JiraSelectSchemaItem[];
}

export interface Sidebar {
  selected?: SidebarOption;
  shown: boolean;
}

export interface ModalsShown {
  createNew?: boolean;
}

export interface QueryBuilderState {
  selectedInstance?: string;
  instances?: JiraSelectInstance[];

  schema: Record<string, Schemas>;

  functions?: JiraSelectFunction[];
  expandedFunctions: string[];

  editor: Editor;
  grid: Grid;
  sidebar: Sidebar;

  modalsShown: ModalsShown;
}
