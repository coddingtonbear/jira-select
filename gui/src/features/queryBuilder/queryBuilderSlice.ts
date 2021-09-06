import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";
import {
  Editor,
  Grid,
  ModalsShown,
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
  sidebar: { shown: false },
  expandedFunctions: [],
  schema: {},
  modalsShown: {},
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
    state.functions = action.payload;
  },
  toggleFunctionExpansion: (
    state: QueryBuilderState,
    action: PayloadAction<string>
  ) => {
    if (state.expandedFunctions.includes(action.payload)) {
      state.expandedFunctions = state.expandedFunctions.filter(
        (val) => val !== action.payload
      );
    } else {
      state.expandedFunctions.push(action.payload);
    }
  },
  setIssueSchema: (
    state: QueryBuilderState,
    action: PayloadAction<JiraSelectSchemaItem[]>
  ) => {
    if (state.selectedInstance) {
      state.schema[state.selectedInstance].issue = action.payload;
    }
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
    if (state.schema[action.payload] === undefined) {
      state.schema[action.payload] = {};
    }
    state.selectedInstance = action.payload;
  },
  showModal: (
    state: QueryBuilderState,
    action: PayloadAction<keyof ModalsShown>
  ) => {
    state.modalsShown[action.payload] = true;
  },
  closeModal: (state: QueryBuilderState) => {
    state.modalsShown = {};
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
  useSelector((s: RootState) => s.queryEditor.functions);

export const useIssueSchema = (): JiraSelectSchemaItem[] | undefined =>
  useSelector((s: RootState) =>
    s.queryEditor.selectedInstance
      ? s.queryEditor.schema[s.queryEditor.selectedInstance].issue
      : []
  );

export const useInstances = (): JiraSelectInstance[] =>
  useSelector((s: RootState) => s.queryEditor.instances);

export const useSelectedInstance = (): string | undefined =>
  useSelector((s: RootState) => s.queryEditor.selectedInstance);

export const useExpandedFunctions = (): string[] =>
  useSelector((s: RootState) => s.queryEditor.expandedFunctions);

export const useModalIsShown = (name: keyof ModalsShown): boolean =>
  useSelector((s: RootState) => Boolean(s.queryEditor.modalsShown[name]));

export default queryBuilderSlice;
