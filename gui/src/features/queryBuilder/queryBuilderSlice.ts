import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";
import { Editor, Grid, QueryBuilderState, SidebarOption } from "./types";
import { executeQuery } from "./thunks";

const initialState: QueryBuilderState = {
  editor: { running: false },
  grid: { columns: [], rows: [] },
};

const reducers = {
  updateGrid: (state: QueryBuilderState, action: PayloadAction<Grid>) => {
    state.grid = action.payload;
  },
  showSidebar: (
    state: QueryBuilderState,
    action: PayloadAction<SidebarOption>
  ) => {
    state.sidebarOption = action.payload;
  },
  hideSidebar: (state: QueryBuilderState) => {
    state.sidebarOption = undefined;
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

export const useSidebarOption = (): SidebarOption | undefined =>
  useSelector((s: RootState) => s.queryEditor.sidebarOption);

export default queryBuilderSlice;
