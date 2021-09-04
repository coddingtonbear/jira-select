import React from "react";
import { useEditorContext } from "../queryBuilderSlice";

import * as monaco from "monaco-editor";
import MonacoEditor from "@monaco-editor/react";

const DEFAULT_VALUE: string = "select:\n- key\nfrom: issues";

const Editor: React.FC = () => {
  const [value, setValue] = React.useState<string | undefined>(DEFAULT_VALUE);
  const { error, running } = useEditorContext();

  const editorOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
    lineNumbers: "off",
    codeLens: false,
    folding: false,
    minimap: { enabled: false },
    scrollbar: { vertical: "hidden", horizontal: "hidden" },
  };

  return (
    <div className="editorContainer">
      <MonacoEditor
        language="yaml"
        value={value}
        onChange={setValue}
        className="editor"
        width=""
        height=""
        options={editorOptions}
      />
      {error && <div className="error">{error} </div>}
      {running && <div className="running">Query in progress...</div>}
    </div>
  );
};

export default Editor;
