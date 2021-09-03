import React from "react";
import Editor from "./Editor";
import Grid from "./Grid";

import { PlayCircleFilled } from "@material-ui/icons";
import { useAppDispatch } from "../../../store";
import { executeQuery } from "../thunks";
import { useEditorValue } from "../queryBuilderSlice";

const QueryBuilder: React.FC = () => {
  const dispatch = useAppDispatch();
  const editorValue = useEditorValue();

  function onExecuteQuery() {
    dispatch(executeQuery(editorValue));
  }

  return (
    <div className="queryBuilder">
      <div className="toolbar">
        <PlayCircleFilled onClick={onExecuteQuery} />
      </div>
      <div className="body">
        <div className="sideBar"></div>
        <Editor />
        <Grid />
      </div>
    </div>
  );
};

export default QueryBuilder;
