import React from "react";
import { useDispatch } from "react-redux";
import { queryBuilderActions } from "../../../store";
import { useEditorContext } from "../queryBuilderSlice";

import * as monaco from "monaco-editor";
import MonacoEditor from "@monaco-editor/react";

const Editor: React.FC = () => {
  const { value, error, running } = useEditorContext();
  const dispatch = useDispatch();

  function onEditorChange(value: string | undefined) {
    dispatch(queryBuilderActions.updateEditorValue(value ?? ""));
  }

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
        onChange={onEditorChange}
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
