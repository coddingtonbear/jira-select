//import { fetch, ResponseType } from '@tauri-apps/api/http'
import { invoke } from "@tauri-apps/api/tauri";

export type QueryRow = Record<string, any>;

export interface RpcResponse {
  stdout: string;
  stderr: string;
  code: number;
}

export async function execute(
  params: string[],
  stdin?: string
): Promise<RpcResponse> {
  return invoke<RpcResponse>("run_jira_select", { params, stdin: stdin ?? "" });
}

export async function executeQuery(
  instance: string,
  query: string
): Promise<QueryRow[]> {
  const result = await execute(
    ["--instance-name", instance, "run-query", "--format=json"],
    query
  );

  if (result.code !== 0) {
    throw new Error(
      `Query execution failed with status ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }

  return JSON.parse(result.stdout);
}

export interface JiraSelectFunction {
  name: string;
  description: string;
  dotpath: string;
  signature?: string;
}

export async function getFunctions(): Promise<JiraSelectFunction[]> {
  const result = await execute(["functions", "--json"]);

  if (result.code !== 0) {
    throw new Error(
      `Error encountered while fetching available functions ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }

  return JSON.parse(result.stdout);
}

export interface JiraSelectSchemaItem {
  id: string;
  type: string;
  description: string | null;
}

export async function getSchema(
  instance: string,
  schema: "boards" | "issues" | "sprints"
): Promise<JiraSelectSchemaItem[]> {
  const result = await execute([
    "--instance-name",
    instance,
    "schema",
    schema,
    "--json",
  ]);

  if (result.code !== 0) {
    throw new Error(
      `Error encountered while fetching schema for ${schema} ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }

  return JSON.parse(result.stdout);
}

export interface JiraSelectInstance {
  name: string;
  url: string;
  username: string;
}

export async function getInstances(): Promise<JiraSelectInstance[]> {
  const result = await execute(["show-instances", "--json"]);

  if (result.code !== 0) {
    throw new Error(
      `Error encountered while fetching instances ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }

  return JSON.parse(result.stdout);
}

export async function setupInstance(
  url: string,
  username: string,
  password: string,
  name: string
): Promise<void> {
  const result = await execute(
    [
      "--instance-name",
      name,
      "--instance-url",
      url,
      "--username",
      username,
      "setup-instance",
    ],
    password
  );

  if (result.code !== 0) {
    throw new Error(
      `Error encountered while setting-up instance ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }
}
