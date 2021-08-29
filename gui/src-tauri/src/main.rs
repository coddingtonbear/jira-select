#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use serde::Serialize;
use tauri::api::process::{Command, CommandEvent};

#[derive(Serialize)]
pub struct JiraSelectResult {
  pub code: i32,
  pub stdout: String,
  pub stderr: String,
}

#[tauri::command]
async fn run_jira_select(params: Vec<&str>, stdin: &str) -> Result<JiraSelectResult, String> {
  let mut stdout: Vec<String> = Vec::new();
  let mut stderr: Vec<String> = Vec::new();
  let mut code: i32 = 0;

  let (mut rx, mut child) = Command::new_sidecar("jira-select")
    .expect("Unable to launch jira-select sidecar.")
    .args(params)
    .spawn()
    .expect("Unable to spawn jira-select subprocess.");

  child.write(stdin.as_bytes()).ok();

  // Delete the subprocess so its stdin pipe will be closed
  drop(child);

  // read events such as stdout
  while let Some(event) = rx.recv().await {
    /*if let CommandEvent::Stdout(line) = event {
      stdout.push(line);
    };
    if let CommandEvent::Stderr(line) = event {
      stderr.push(line);
    };*/
    match event {
      CommandEvent::Stdout(line) => {
        stdout.push(line);
      }
      CommandEvent::Stderr(line) => {
        stderr.push(line);
      }
      CommandEvent::Terminated(result) => {
        code = result.code.ok_or(-1).expect("Could not get status");
      }
      _ => {}
    }
  }

  Ok(JiraSelectResult {
    code: code,
    stderr: stderr.join("\n"),
    stdout: stdout.join("\n"),
  })
}

fn main() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![run_jira_select])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
