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

const initialState: QueryBuilderState = {
  editor: { running: false },
  grid: { columns: [], rows: [] },
  sidebar: { shown: false },
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

export default queryBuilderSlice;
