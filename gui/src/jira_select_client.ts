//import { fetch, ResponseType } from '@tauri-apps/api/http'
import { invoke } from '@tauri-apps/api/tauri'

type QueryRow = Record<string, any>

interface RpcResponse {
  stdout: string
  stderr: string
  code: number
}

export async function executeQuery(query: string): Promise<RpcResponse> {
  console.log("Running command")
  const result = await invoke<RpcResponse>('run_jira_select', {params: ["run-query", "--format=json"], stdin: query})

  console.log("Result", result)
  return result
}
