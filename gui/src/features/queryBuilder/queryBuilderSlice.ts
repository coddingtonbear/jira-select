import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";
import { Grid, QueryBuilderState } from "./types";

const initialState: QueryBuilderState = {
  editor: { value: "select:\n- key\nfrom: issues" },
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
});

export default queryBuilderSlice;

export const useEditorValue = (): string =>
  useSelector((s: RootState) => s.queryEditor.editor.value);

export const useGridContext = (): Grid =>
  useSelector((s: RootState) => s.queryEditor.grid);
