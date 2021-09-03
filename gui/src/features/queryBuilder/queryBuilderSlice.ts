import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import { RootState } from "../../store";

interface QueryBuilderState {
  editor: {
    value: string;
  };
}

const initialState: QueryBuilderState = {
  editor: { value: "" },
};

const reducers = {
  updateEditorValue: (
    state: QueryBuilderState,
    action: PayloadAction<string>
  ) => {
    state.editor.value = action.payload;
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
