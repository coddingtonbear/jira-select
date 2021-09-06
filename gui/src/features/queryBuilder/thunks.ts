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

  if (
    state.queryEditor.schema[state.queryEditor.selectedInstance].issue !==
    undefined
  ) {
    return;
  }

  const schema = await client.getSchema(
    state.queryEditor.selectedInstance,
    "issues"
  );

  thunkAPI.dispatch(queryBuilderSlice.actions.setIssueSchema(schema));
});

export const populateInstanceList = createAsyncThunk<
  void,
  void,
  { state: RootState }
>("queryBuilder/populateInstanceList", async (_, thunkAPI) => {
  const instances = await client.getInstances();

  const state = thunkAPI.getState();

  thunkAPI.dispatch(queryBuilderSlice.actions.setInstances(instances));
  if (
    state.queryEditor.selectedInstance === undefined &&
    instances.length > 0
  ) {
    thunkAPI.dispatch(
      queryBuilderSlice.actions.setSelectedInstance(instances[0].name)
    );
  }
});

export interface SetupInstanceRequest {
  username: string;
  password: string;
  url: string;
  name: string;
}

export const setupInstance = createAsyncThunk<
  void,
  SetupInstanceRequest,
  { state: RootState }
>("queryBuilder/setupInstance", async (params, thunkAPI) => {
  await client.setupInstance(
    params.url,
    params.username,
    params.password,
    params.name
  );

  thunkAPI.dispatch(populateInstanceList());
});
