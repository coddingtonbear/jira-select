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

export async function executeQuery(query: string): Promise<QueryRow[]> {
  const result = await execute(["run-query", "--format=json"], query);

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
  schema: "boards" | "issues" | "sprints"
): Promise<JiraSelectSchemaItem[]> {
  const result = await execute(["schema", schema, "--json"]);

  if (result.code !== 0) {
    throw new Error(
      `Error encountered while fetching scheamma for ${schema} ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    );
  }

  return JSON.parse(result.stdout);
}
