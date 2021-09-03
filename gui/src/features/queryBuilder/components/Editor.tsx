import React from "react";
import { useDispatch } from "react-redux";
import { queryBuilderActions } from "../../../store";
import { useEditorValue } from "../queryBuilderSlice";

import * as monaco from "monaco-editor";
import MonacoEditor, { loader } from "@monaco-editor/react";

loader.config({
  paths: {
    vs: "../node_modules/monaco-editor/min/vs",
  },
});

const Editor: React.FC = () => {
  const editorValue = useEditorValue();
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
    <MonacoEditor
      language="yaml"
      value={editorValue}
      onChange={onEditorChange}
      className="editor"
      width=""
      height=""
      options={editorOptions}
    />
  );
};

export default Editor;
