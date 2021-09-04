import React from "react";
import { useEditorContext } from "../queryBuilderSlice";
import { executeQuery } from "../thunks";

import * as monaco from "monaco-editor";
import MonacoEditor from "@monaco-editor/react";
import { useAppDispatch } from "../../../store";
import ReactLoading from "react-loading";
import { PlayCircleOutline } from "@material-ui/icons";

const DEFAULT_VALUE: string = "select:\n- key\nfrom: issues";

const Editor: React.FC = () => {
  const [value, setValue] = React.useState<string | undefined>(DEFAULT_VALUE);
  const { error, running } = useEditorContext();
  const dispatch = useAppDispatch();

  const editorOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
    lineNumbers: "off",
    codeLens: false,
    folding: false,
    minimap: { enabled: false },
    scrollbar: { vertical: "hidden", horizontal: "hidden" },
  };

  function onRunQuery() {
    dispatch(executeQuery(value ?? ""));
  }

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
      <div className="buttons">
        <button onClick={onRunQuery}>
          <PlayCircleOutline />
        </button>
        {running && <ReactLoading type="bars" />}
      </div>
    </div>
  );
};

export default Editor;
