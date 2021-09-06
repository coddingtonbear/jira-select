import React from "react";
import slice, { useEditorContext, useInsertString } from "../queryBuilderSlice";
import { executeQuery } from "../thunks";

import * as monaco from "monaco-editor";
import MonacoEditor from "@monaco-editor/react";
import { useAppDispatch } from "../../../store";
import { PlayCircleOutline } from "@material-ui/icons";
import LoadingIndicator from "./LoadingIndicator";

const DEFAULT_VALUE: string = "select:\n- key\nfrom: issues";

const Editor: React.FC = () => {
  const editorRef = React.useRef<monaco.editor.IStandaloneCodeEditor>();

  const [value, setValue] = React.useState<string | undefined>(DEFAULT_VALUE);
  const { error, running } = useEditorContext();
  const insertString = useInsertString();

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    if (insertString && editorRef.current) {
      const range = editorRef.current.getSelection();

      if (range) {
        editorRef.current?.executeEdits("insert-string", [
          {
            range: range,
            text: insertString,
            forceMoveMarkers: true,
          },
        ]);
      }
    }
    dispatch(slice.actions.insertTextAtCursorCompleted());
  }, [insertString, dispatch]);

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

  function onEditorMounted(editor: monaco.editor.IStandaloneCodeEditor) {
    editorRef.current = editor;
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
        onMount={onEditorMounted}
      />
      {error && <div className="error">{error} </div>}
      <div className="buttons">
        <PlayCircleOutline onClick={onRunQuery} />
        {running && <LoadingIndicator />}
      </div>
    </div>
  );
};

export default Editor;
