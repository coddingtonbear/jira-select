import React from 'react';
import logo from './logo.svg';
import './App.css';

import { executeQuery } from './jira_select_client';
//import { ChildProcess } from '@tauri-apps/api/shell';


function App() {
  //const [server, setServer] = React.useState<ChildProcess>()
  //const [output, setOutput] = React.useState<Record<string, any>>({})
  const [stdout, setStdout] = React.useState<string>('')
  const [stderr, setStderr] = React.useState<string>('')
  const [code, setCode] = React.useState<number>(-2)

  function runQuery(): void {
    executeQuery(`
      select:
      - id
      from: issues
    `).then((results) => {
      console.log("Result returned")
      setCode(results.code)
      setStderr(results.stderr)
      setStdout(results.stdout)
    }).catch((e) => {
      console.log("Error returned")
      setCode(-3)
      setStdout('')
      setStderr(e.toString())
    })
  }

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>code: {code}</p>
        <p>stderr: {stderr}</p>
        <p>stdout: {stdout}</p>
        <button onClick={runQuery}>Click Me</button>
      </header>
    </div>
  );
}

export default App;
