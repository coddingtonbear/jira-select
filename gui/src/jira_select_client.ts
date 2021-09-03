//import { fetch, ResponseType } from '@tauri-apps/api/http'
import { invoke } from '@tauri-apps/api/tauri'

export type QueryRow = Record<string, any>

export interface RpcResponse {
  stdout: string
  stderr: string
  code: number
}

export async function execute(params: string[], stdin: string): Promise<RpcResponse> {
  return invoke<RpcResponse>('run_jira_select', {params, stdin})
}

export async function executeQuery(query: string): Promise<QueryRow[]> {
  const result = await execute(["run-query", "--format=json"], query)

  if (result.code !== 0) {
    throw new Error(
      `Query execution failed with status ${result.code}: stderr: ${result.stderr}; stdout: ${result.stdout}`
    )
  }

  return JSON.parse(result.stdout)
}
