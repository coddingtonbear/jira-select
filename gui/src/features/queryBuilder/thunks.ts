import { createAsyncThunk } from "@reduxjs/toolkit";
import * as client from "../../jira_select_client";
import { queryBuilderActions } from "../../store";
import { Column } from "./types";

export const executeQuery = createAsyncThunk<void, string>(
  "queryBuilder/executeQuery",
  async (payload, thunkAPI) => {
    const results = await client.executeQuery(payload);

    const columns: Column[] = [];
    if (results) {
      for (const k in results[0]) {
        columns.push({ key: k, name: k });
      }
    }

    thunkAPI.dispatch(
      queryBuilderActions.updateGrid({
        columns: columns,
        rows: results,
      })
    );
  }
);
