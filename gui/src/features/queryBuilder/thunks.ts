import { createAsyncThunk } from "@reduxjs/toolkit";
import * as client from "../../jira_select_client";
import { Column } from "./types";
import queryBuilderSlice from "./queryBuilderSlice";
import { RootState } from "../../store";

export const executeQuery = createAsyncThunk<
  void,
  string,
  { state: RootState }
>("queryBuilder/executeQuery", async (payload, thunkAPI) => {
  const state = thunkAPI.getState();

  if (!state.queryEditor.selectedInstance) {
    throw Error("No instance selected");
  }

  const results = await client.executeQuery(
    state.queryEditor.selectedInstance,
    payload
  );
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
});

export const populateFunctionList = createAsyncThunk<void, void>(
  "queryBuilder/populateFunctions",
  async (_, thunkAPI) => {
    const functions = await client.getFunctions();

    thunkAPI.dispatch(queryBuilderSlice.actions.setFunctions(functions));
  }
);

export const populateIssueSchema = createAsyncThunk<
  void,
  void,
  { state: RootState }
>("queryBuilder/populateIssueSchema", async (_, thunkAPI) => {
  const state = thunkAPI.getState();
  if (!state.queryEditor.selectedInstance) {
    throw Error("No instance selected");
  }

  const schema = await client.getSchema(
    state.queryEditor.selectedInstance,
    "issues"
  );

  thunkAPI.dispatch(queryBuilderSlice.actions.setIssueSchema(schema));
});

export const populateInstanceList = createAsyncThunk<void, void>(
  "queryBuilder/populateInstanceList",
  async (_, thunkAPI) => {
    const instances = await client.getInstances();

    thunkAPI.dispatch(queryBuilderSlice.actions.setInstances(instances));
  }
);
