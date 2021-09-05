import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";
import {
  Editor,
  Grid,
  QueryBuilderState,
  Sidebar,
  SidebarOption,
} from "./types";
import { executeQuery } from "./thunks";
import {
  JiraSelectFunction,
  JiraSelectInstance,
  JiraSelectSchemaItem,
} from "../../jira_select_client";

const initialState: QueryBuilderState = {
  instances: [],
  editor: { running: false },
  grid: { columns: [], rows: [] },
  sidebar: { shown: false, schema: {} },
};

const reducers = {
  updateGrid: (state: QueryBuilderState, action: PayloadAction<Grid>) => {
    state.grid = action.payload;
  },
  showSidebar: (
    state: QueryBuilderState,
    action: PayloadAction<SidebarOption>
  ) => {
    state.sidebar.selected = action.payload;
    state.sidebar.shown = true;
  },
  hideSidebar: (state: QueryBuilderState) => {
    state.sidebar.shown = false;
  },
  insertTextAtCursor: (
    state: QueryBuilderState,
    action: PayloadAction<string>
  ) => {
    state.editor.insertString = action.payload;
  },
  insertTextAtCursorCompleted: (state: QueryBuilderState) => {
    state.editor.insertString = undefined;
  },
  setFunctions: (
    state: QueryBuilderState,
    action: PayloadAction<JiraSelectFunction[]>
  ) => {
    state.sidebar.functions = action.payload;
  },
  clearIssueSchema: (state: QueryBuilderState) => {
    state.sidebar.schema.issue = undefined;
  },
  setIssueSchema: (
    state: QueryBuilderState,
    action: PayloadAction<JiraSelectSchemaItem[]>
  ) => {
    state.sidebar.schema.issue = action.payload;
  },
  setInstances: (
    state: QueryBuilderState,
    action: PayloadAction<JiraSelectInstance[]>
  ) => {
    state.instances = action.payload;
  },
  setSelectedInstance: (
    state: QueryBuilderState,
    action: PayloadAction<string>
  ) => {
    state.selectedInstance = action.payload;
  },
};

const queryBuilderSlice = createSlice<
  QueryBuilderState,
  typeof reducers,
  "queryBuilder"
>({
  name: "queryBuilder",
  initialState,
  reducers,
  extraReducers: (builder) => {
    builder.addCase(executeQuery.pending, (state) => {
      state.editor.error = undefined;
      state.editor.running = true;
    });
    builder.addCase(executeQuery.fulfilled, (state) => {
      state.editor.running = false;
    });
    builder.addCase(executeQuery.rejected, (state, { error }) => {
      state.editor.error = error.message;
      state.editor.running = false;
    });
  },
});

export const useEditorContext = (): Editor =>
  useSelector((s: RootState) => s.queryEditor.editor);

export const useGridContext = (): Grid =>
  useSelector((s: RootState) => s.queryEditor.grid);

export const useSidebarContext = (): Sidebar =>
  useSelector((s: RootState) => s.queryEditor.sidebar);

export const useInsertString = (): string | undefined =>
  useSelector((s: RootState) => s.queryEditor.editor.insertString);

export const useFunctionList = (): JiraSelectFunction[] | undefined =>
  useSelector((s: RootState) => s.queryEditor.sidebar.functions);

export const useIssueSchema = (): JiraSelectSchemaItem[] | undefined =>
  useSelector((s: RootState) => s.queryEditor.sidebar.schema.issue);

export const useInstances = (): JiraSelectInstance[] =>
  useSelector((s: RootState) => s.queryEditor.instances);

export const useSelectedInstance = (): string | undefined =>
  useSelector((s: RootState) => s.queryEditor.selectedInstance);

export default queryBuilderSlice;
