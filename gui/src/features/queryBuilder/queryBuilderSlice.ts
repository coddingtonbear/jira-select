import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";
import { Editor, Grid, QueryBuilderState } from "./types";
import { executeQuery } from "./thunks";

const initialState: QueryBuilderState = {
  editor: { value: "select:\n- key\nfrom: issues", running: false },
  grid: { columns: [], rows: [] },
};

const reducers = {
  updateEditorValue: (
    state: QueryBuilderState,
    action: PayloadAction<string>
  ) => {
    state.editor.value = action.payload;
  },
  updateGrid: (state: QueryBuilderState, action: PayloadAction<Grid>) => {
    state.grid = action.payload;
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

export default queryBuilderSlice;

export const useEditorContext = (): Editor =>
  useSelector((s: RootState) => s.queryEditor.editor);

export const useGridContext = (): Grid =>
  useSelector((s: RootState) => s.queryEditor.grid);
