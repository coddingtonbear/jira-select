import { createAsyncThunk } from "@reduxjs/toolkit";
import * as client from "../../jira_select_client";
import { Column } from "./types";
import queryBuilderSlice from "./queryBuilderSlice";

export const executeQuery = createAsyncThunk<void, string>(
  "queryBuilder/executeQuery",
  async (payload, thunkAPI) => {
    const results = await client.executeQuery(payload);
    const processedResults: Record<string, string>[] = [];

    const columns: Column[] = [];
    if (results) {
      for (const k in results[0]) {
        columns.push({ key: k, name: k });
      }
    }

    for (const result of results) {
      const processedResult: Record<string, string> = {};

      for (const field in result) {
        const value = result[field];

        if (typeof value === "string") {
          processedResult[field] = value;
        } else if (typeof value === "number") {
          processedResult[field] = value.toString();
        } else {
          processedResult[field] = JSON.stringify(value);
        }
      }

      processedResults.push(processedResult);
    }

    thunkAPI.dispatch(
      queryBuilderSlice.actions.updateGrid({
        columns: columns,
        rows: processedResults,
      })
    );
  }
);
